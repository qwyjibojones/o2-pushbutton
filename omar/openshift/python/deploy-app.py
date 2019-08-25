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

final_return_code = 0
namespace_deployment_pairs = []


# Add any deployments from new_deployments that aren't in old_deployments to the list to track at the end of the phase
def add_new_deployments_from_namespace(namespace, old_deployments, new_deployments):
    global namespace_deployment_pairs
    deployments_to_add = []
    for deployment in new_deployments:
        if deployment == '':
            continue
        if deployment not in old_deployments:
            deployments_to_add.append(deployment)

    for deployment in deployments_to_add:
        namespace_deployment_pairs.append([namespace, deployment])


# Process all apps defined in the deployConfig.yml file in order of phases
def process_all(config_file, template_dir, configmap_dir, overrides, remove_app, deploy_app, abort_on_failure, wait_for_pods, phases):
    global final_return_code
    all_phases = parse_deploy_sequence.get_deployment_phases(config_file)

    if phases is None:
        run_phases = all_phases
    else:
        run_phases = []
        for phase_num in phases:
            if phase_num > len(all_phases):
                logging.warn('Phase %i does not exist, skipping' % phase_num)
                continue
            run_phases.append(all_phases[phase_num-1])

    for phase in run_phases:
        run_phase(abort_on_failure, config_file, configmap_dir, deploy_app, overrides, phase, remove_app, template_dir, wait_for_pods)


def run_phase(abort_on_failure, config_file, configmap_dir, deploy_app, overrides, phase, remove_app, template_dir, wait_for_pods):
    global final_return_code
    global namespace_deployment_pairs
    namespace_deployment_pairs = []
    logging.info('\n####### Running phase #######')

    phase_processes = {}
    for app_name in phase:
        new_app_process = process_app(config_file=config_file,
                                      template_dir=template_dir,
                                      configmap_dir=configmap_dir,
                                      overrides=overrides,
                                      app_name=app_name,
                                      remove_app=remove_app,
                                      deploy_app=deploy_app,
                                      wait_for_pods=wait_for_pods)
        phase_processes[app_name] = new_app_process

    logging.info('Waiting for apps...\n')

    if wait_for_pods:
        for [namespace, deployment] in namespace_deployment_pairs:
            wait_counter = 30
            while int(openshift.get_available_replicas_for_deployment(namespace=namespace,
                                                                  deployment=deployment)) == 0:
                logging.info('Waiting for deployment %s in namespace %s' % (deployment, namespace))
                time.sleep(5)
                wait_counter -= 1
                if wait_counter <= 0:
                    logging.warn('Timed out waiting for deployment %s in namespace %s, continuing' % (deployment, namespace))
                    break

    for app_name, process in phase_processes.iteritems():
        if process is not None:
            process.wait()
            return_code = helpers.report_status(name=app_name,
                                                process=process)
            if return_code != 0:
                final_return_code = return_code
                if abort_on_failure:
                    exit(return_code)


def process_app(config_file, template_dir, configmap_dir, overrides, app_name, remove_app, deploy_app, wait_for_pods):
    logging.info('\n####### Processing application: %s #######' % app_name)

    app_params = parse_deploy_sequence.get_params_for_service(config_file=config_file,
                                                              overrides=overrides,
                                                              service_name=app_name)
    logging.debug('Using params: %s' % json.dumps(app_params))

    process = None
    if app_params['type'] == 'configmap':
        process =process_configmap(app_name=app_name,
                                 configmap_dir=configmap_dir,
                                 app_params=app_params,
                                 remove_app=remove_app,
                                 deploy_app=deploy_app)
    else:
        namespace = app_params['namespace']
        old_deployments = None
        if wait_for_pods:
            old_deployments = openshift.get_deployment_configs(namespace=namespace)

        process = process_template(app_name=app_name,
                                template_dir=template_dir,
                                app_params=app_params,
                                remove_app=remove_app,
                                deploy_app=deploy_app)

        if wait_for_pods:
            new_deployments = openshift.get_deployment_configs(namespace=namespace)
            add_new_deployments_from_namespace(namespace=namespace,
                                               old_deployments=old_deployments,
                                               new_deployments=new_deployments)

    return process


# Config maps are special and need to be handled differently from other apps
# This currently only supports loading config maps from files, rather than a template
# However, if a template exists that is supported by `oc new-app`, it can be used with process_template
def process_configmap(app_name, configmap_dir, app_params, remove_app, deploy_app):
    full_fromfile_path = get_fromfile_path(app_name=app_name,
                                           configmap_dir=configmap_dir,
                                           app_params=app_params)

    if remove_app:
        logging.info('Removing existing configmap %s' % app_name)
        openshift.remove_configmap(app_name, namespace=app_params['namespace'])

    if deploy_app:
        logging.info('Adding configmap %s' % app_name)
        deploy_process = openshift.create_configmap(name=app_name,
                                                    fromfile=full_fromfile_path,
                                                    namespace=app_params['namespace'],
                                                    wait=True)
        return deploy_process


def process_template(app_name, template_dir, app_params, remove_app, deploy_app):
    full_template_path = get_template_path(app_name=app_name,
                                           template_dir=template_dir,
                                           app_params=app_params)

    if remove_app:
        logging.info('Removing existing deployment for %s' % app_name)
        openshift.remove_objects_in_processed_template(processed_file=openshift.process_template(template_file=full_template_path,
                                                                                                 params=app_params),
                                                       wait=True)

    if deploy_app:
        logging.info('Deploying app %s' % app_name)
        deploy_process = openshift.new_app(template_file=full_template_path,
                                           params=app_params,
                                           wait=True)
        return deploy_process


def get_template_path(app_name, template_dir, app_params):
    if template_dir is None:
        raise Exception('Template dir must be specified if deploying from templates')

    if 'template_file' not in app_params:
        raise Exception('Template file not specified for app %s' % app_name)

    full_template_path = os.path.join(template_dir, app_params['template_file'])
    if not os.path.isfile(full_template_path):
        raise Exception('Template file at %s does not exist or is not a file' % full_template_path)

    return full_template_path


def get_fromfile_path(app_name, configmap_dir, app_params):
    if configmap_dir is None:
        raise Exception('Configmap dir must be specified if deploying config maps from files')

    if 'from-file' not in app_params:
        raise Exception('Fromfile not specified for app %s' % app_name)

    full_configmap_path = os.path.join(configmap_dir, app_params['from-file'])
    if not os.path.exists(full_configmap_path):
        raise Exception('Configmap path at %s does not exist' % full_configmap_path)

    return full_configmap_path


def main(args):
    global final_return_code
    parsed_args = argument_parser.parse_args(args)
    logging.getLogger().setLevel(getattr(logging, parsed_args.loglevel))
    logging.info('Using config file: %s\nand template dir:%s' % (parsed_args.config_file, parsed_args.template_dir))

    openshift.set_oc_location(parsed_args.oc_location)

    openshift.login(openshift_url=parsed_args.openshift_url,
                    username=os.getenv('OPENSHIFT_USERNAME'),
                    password=os.getenv('OPENSHIFT_PASSWORD'))

    if parsed_args.all:
        process_all(config_file=parsed_args.config_file,
                    template_dir=parsed_args.template_dir,
                    configmap_dir=parsed_args.configmap_dir,
                    overrides=parsed_args.overrides,
                    remove_app=parsed_args.remove,
                    deploy_app=not parsed_args.nodeploy,
                    abort_on_failure=parsed_args.abort_on_failure,
                    wait_for_pods=parsed_args.wait_for_pods,
                    phases=parsed_args.phases)
    else:
        deploy_process = process_app(config_file=parsed_args.config_file,
                                     template_dir=parsed_args.template_dir,
                                     configmap_dir=parsed_args.configmap_dir,
                                     overrides=parsed_args.overrides,
                                     app_name=parsed_args.service,
                                     remove_app=parsed_args.remove,
                                     deploy_app=not parsed_args.nodeploy)

        if deploy_process is not None:
            final_return_code = helpers.report_status(process=deploy_process, name=parsed_args.service)

        if wait_for_pods:
            pass  # TODO: implement

    exit(final_return_code)


if __name__ == '__main__':
    main(sys.argv[1:])
