import argparse
import sys
import logging
import json
import os
import time

import parse_deploy_sequence
import openshift
import helpers

logging.basicConfig(format='%(message)s', level=logging.INFO)
# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument('-c', '--config-file', required=True, help='The deployConfig yml file to use')
argument_parser.add_argument('-o', '--openshift-url', required=True, help='The url of the openshift instance to deploy to')
argument_parser.add_argument('-t', '--template-dir', default=None, required=False, help='The directory where the openshift template files are located')
argument_parser.add_argument('-m', '--configmap-dir', default=None, required=False, help='The directory where the configmap files are located')
argument_parser.add_argument('--all', required=False, action='store_true', help='Deploy all objects defined in the deployConfig file')
argument_parser.add_argument('-s', '--service', required=False, help='Deploy the provided service. Overridden by the \'--all\' flag')
argument_parser.add_argument('--remove', required=False, action='store_true', help='Remove existing objects first')
argument_parser.add_argument('--nodeploy', required=False, action='store_true', help='Avoid deploying apps, just remove them')
argument_parser.add_argument('--loglevel', default='INFO', type=str.upper, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL'], help='The log level to use')
argument_parser.add_argument('--abort-on-failure', action='store_true', help='Abort the process when there is an error')
argument_parser.add_argument('--phases', type=int, nargs='*', help='The phases to run')
argument_parser.add_argument('--oc-location', default=None, help='The location of the oc executable, if it must be manually specified')
argument_parser.add_argument('--wait-for-pods', action='store_true', help='Wait for all pods to be ready before moving onto the next phase')
argument_parser.add_argument('--overrides', nargs='*', default=[], help='A set of key-value pairs to override settings in the config file')


class Deployer:
    def __init__(self, parsed_args):
        self.final_return_code = 0

        self.config_file = parsed_args.config_file
        self.template_dir = parsed_args.template_dir
        self.configmap_dir = parsed_args.configmap_dir
        self.overrides = parsed_args.overrides
        self.remove_app = parsed_args.remove
        self.deploy_app = not parsed_args.nodeploy
        self.abort_on_failure = parsed_args.abort_on_failure
        self.wait_for_pods = parsed_args.wait_for_pods
        self.requested_phase_numbers = parsed_args.phases

        self.all_defined_phases = []
        self.app_configs = {}

        self.load_config()
        self.tracked_deployments = []
        self.failed_app_deployments = []

    # Add a namespace, deployment_name combination to a list. Used to track which deployments were created by an app
    def mark_deployment_for_tracking(self, app_name, namespace, deployment_name):
        self.tracked_deployments.append((app_name, namespace, deployment_name))

    # Wait for all tracked deployments to complete, returning True if they all succeeded, and False otherwise
    def wait_for_tracked_deployments(self):
        total_success = True
        for (app_name, namespace, deployment_name) in self.tracked_deployments:
            success = self.wait_for_deployment(namespace, deployment_name)
            if not success:
                total_success = False
                self.failed_app_deployments.append((app_name, namespace, deployment_name))
        return total_success

    # Wait for a single deployment in the given namespace
    def wait_for_deployment(self, namespace, deployment_name):
        wait_counter = 30
        while int(openshift.get_available_replicas_for_deployment(namespace=namespace,
                                                                  deployment=deployment_name)) == 0:
            logging.info('Waiting for deployment %s in namespace %s' % (deployment_name, namespace))
            time.sleep(5)
            wait_counter -= 1
            if wait_counter <= 0:
                logging.warn(
                    'Timed out waiting for deployment %s in namespace %s, continuing' % (deployment_name, namespace))
                return False
        return True

    # Load a config file and store information in a more useful format
    def load_config(self):
        loaded_config = parse_deploy_sequence.load_deployment_config(self.config_file)
        all_app_configs = parse_deploy_sequence.generate_app_configs(loaded_config, self.overrides)
        self.app_configs = all_app_configs

        self.all_defined_phases = parse_deploy_sequence.get_simplified_phases_from_config(loaded_config)

    # Process all phases requested
    def process_phases(self):
        phases_to_run = self.all_defined_phases

        # Determine which phases were requested and queue them up to run
        if self.requested_phase_numbers is not None:
            phases_to_run = []
            for phase_num in self.requested_phase_numbers:
                if phase_num > len(self.all_defined_phases):
                    logging.warn('Phase %i does not exist, skipping' % phase_num)
                    continue
                phases_to_run.append(self.all_defined_phases[phase_num - 1])

        for phase in phases_to_run:
            self.run_phase(phase)

        return self.final_return_code

    def run_phase(self, phase):
        logging.info('\n####### Running phase #######')

        # Wipe the tracked deployments for the new phase
        self.tracked_deployments = []
        self.failed_app_deployments = []

        phase_processes = {}
        for app_name in phase:
            new_app_process = self.process_app(app_name)
            phase_processes[app_name] = new_app_process

        for app_name, process in phase_processes.iteritems():
            if process is not None:
                process.wait()
                return_code = helpers.report_status(name=app_name,
                                                    process=process)
                if return_code != 0:
                    self.final_return_code = return_code
                    if should_error_out(self.abort_on_failure, self.app_configs[app_name]):
                        exit(return_code)

        if self.wait_for_pods:
            deployments_successful = self.wait_for_tracked_deployments()
            if not deployments_successful:
                for (app_name, namespace, deployment) in self.failed_app_deployments:
                    if should_error_out(self.abort_on_failure, self.app_configs[app_name]):
                        logging.error("App %s failed to deploy, aborting..." % app_name)
                        exit(1)

        return deployments_successful

    def process_app(self, app_name):
        app_params = self.app_configs[app_name]
        logging.debug('Using params: %s' % json.dumps(app_params))

        process = None
        if app_params['type'] == 'configmap':
            process = self.process_configmap(app_name=app_name)
        else:
            process = self.process_template(app_name=app_name)
        return process

    # Config maps are special and need to be handled differently from other apps
    # This currently only supports loading config maps from files, rather than a template
    # However, if a template exists that is supported by `oc new-app`, it can be used with process_template
    def process_configmap(self, app_name):
        app_params = self.app_configs[app_name]
        full_fromfile_path = helpers.get_fromfile_path(app_name=app_name,
                                                    app_params=self.app_configs[app_name],
                                                    configmap_dir=self.configmap_dir)

        if self.remove_app:
            logging.info('Removing existing configmap %s' % app_name)
            openshift.remove_configmap(app_name, namespace=app_params['namespace'])

        if self.deploy_app:
            logging.info('Adding configmap %s' % app_name)
            deploy_process = openshift.create_configmap(name=app_name,
                                                        fromfile=full_fromfile_path,
                                                        namespace=app_params['namespace'],
                                                        wait=True)
            return deploy_process

    # Process a standard openshift template
    def process_template(self, app_name):
        full_template_path = helpers.get_template_path(app_name=app_name,
                                                       app_params=self.app_configs[app_name],
                                                       template_dir=self.template_dir)
        app_params = self.app_configs[app_name]
        namespace = app_params['namespace']

        if self.remove_app:
            logging.info('Removing existing deployment for %s' % app_name)
            openshift.remove_objects_in_processed_template(
                processed_file=openshift.process_template(template_file=full_template_path,
                                                          params=app_params))

        if self.deploy_app:
            old_deployments = None
            if self.wait_for_pods:
                old_deployments = openshift.get_deployment_configs(namespace=namespace)

            logging.info('Deploying app %s' % app_name)
            deploy_process = openshift.new_app(template_file=full_template_path,
                                               params=app_params,
                                               wait=True)

            if self.wait_for_pods:
                new_deployments = openshift.get_deployment_configs(namespace=namespace)

                for deployment in new_deployments:
                    if deployment == '':
                        continue
                    if deployment not in old_deployments:
                        self.mark_deployment_for_tracking(app_name, namespace, deployment)

            return deploy_process


def should_error_out(abort_on_failure, app_params):
    # Should abort ever?
    if abort_on_failure:
        # Is ignore_errors=True (default) overridden in the app params?
        if 'ignore_errors' not in app_params:
            return True

        if not app_params['ignore_errors']:
            return True

    return False


def main(args):
    parsed_args = argument_parser.parse_args(args)
    logging.getLogger().setLevel(getattr(logging, parsed_args.loglevel))
    logging.info('Using config file: %s\nand template dir:%s' % (parsed_args.config_file, parsed_args.template_dir))

    final_return_code = 0

    openshift.set_oc_location(parsed_args.oc_location)

    openshift.login(openshift_url=parsed_args.openshift_url,
                    username=os.getenv('OPENSHIFT_USERNAME'),
                    password=os.getenv('OPENSHIFT_PASSWORD'))

    deployer = Deployer(parsed_args)

    if parsed_args.all:
        final_return_code = deployer.process_phases()
    else:
        deploy_process = deployer.process_app(parsed_args.service)

        if deploy_process is not None:
            final_return_code = helpers.report_status(process=deploy_process, name=parsed_args.service)

        if parsed_args.wait_for_pods:
            deployer.wait_for_tracked_deployments()

    exit(final_return_code)


if __name__ == '__main__':
    main(sys.argv[1:])
