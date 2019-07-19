import argparse
import sys
import logging
import json
import os

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
argument_parser.add_argument('--start-phase', type=int, default=1, help='The phase to start with, the first phase (1) by default')
argument_parser.add_argument('overrides', nargs='*', help='A set of key-value pairs to override settings in the config file')

final_return_code = 0


# Process all apps defined in the deployConfig.yml file in order of phases
def process_all(config_file, template_dir, configmap_dir, overrides, remove_app, deploy_app, abort_on_failure, start_phase):
    global final_return_code
    phases = parse_deploy_sequence.get_deployment_phases(config_file)
    phase_counter = start_phase-1
    for phase in phases[start_phase-1:]:
        phase_counter += 1
        logging.info('\n####### Running phase %s #######' % phase_counter)
        phase_processes = {}
        for app_name in phase:
            new_app_process = process_app(config_file=config_file,
                                          template_dir=template_dir,
                                          configmap_dir=configmap_dir,
                                          overrides=overrides,
                                          app_name=app_name,
                                          remove_app=remove_app,
                                          deploy_app=deploy_app,
                                          wait=False)
            phase_processes[app_name] = new_app_process

        logging.info('Waiting for apps...\n')
        for app_name, process in phase_processes.iteritems():
            if process is not None:
                process.wait()
                return_code = helpers.report_status(name=app_name,
                                      process=process)
                if return_code != 0:
                    final_return_code = return_code
                    if abort_on_failure:
                        exit(return_code)


def process_app(config_file, template_dir, configmap_dir, overrides, app_name, remove_app, deploy_app, wait):
    logging.info('\n####### Processing application: %s #######' % app_name)

    app_params = parse_deploy_sequence.get_params_for_service(config_file=config_file,
                                                              overrides=overrides,
                                                              service_name=app_name)
    logging.debug('Using params: %s' % json.dumps(app_params))

    if app_params['type'] == 'configmap':
        return process_configmap(app_name=app_name,
                                 configmap_dir=configmap_dir,
                                 app_params=app_params,
                                 remove_app=remove_app,
                                 deploy_app=deploy_app,
                                 wait=wait)

    else:
        return process_template(app_name=app_name,
                                template_dir=template_dir,
                                app_params=app_params,
                                remove_app=remove_app,
                                deploy_app=deploy_app,
                                wait=wait)


# Config maps are special and need to be handled differently from other apps
# This currently only supports loading config maps from files, rather than a template
# However, if a template exists that is supported by `oc new-app`, it can be used with process_template
def process_configmap(app_name, configmap_dir, app_params, remove_app, deploy_app, wait):
    full_fromfile_path = get_fromfile_path(app_name=app_name,
                                           configmap_dir=configmap_dir,
                                           app_params=app_params)

    if remove_app:
        logging.info('Removing existing configmap %s' % app_name)
        openshift.remove_configmap(app_name, namespace=app_params['DEPLOYMENT_TARGET'])

    if deploy_app:
        logging.info('Adding configmap %s' % app_name)
        deploy_process = openshift.create_configmap(name=app_name,
                                                    fromfile=full_fromfile_path,
                                                    namespace=app_params['DEPLOYMENT_TARGET'],
                                                    wait=wait)
        return deploy_process


def process_template(app_name, template_dir, app_params, remove_app, deploy_app, wait):
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
                                           wait=wait)
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
                    start_phase=parsed_args.start_phase)
    else:
        deploy_process = process_app(config_file=parsed_args.config_file,
                                     template_dir=parsed_args.template_dir,
                                     configmap_dir=parsed_args.configmap_dir,
                                     overrides=parsed_args.overrides,
                                     app_name=parsed_args.service,
                                     remove_app=parsed_args.remove,
                                     deploy_app= not parsed_args.nodeploy,
                                     wait=True)
        if deploy_process is not None:
            final_return_code = helpers.report_status(process=deploy_process, name=parsed_args.service)

    exit(final_return_code)


if __name__ == '__main__':
    main(sys.argv[1:])
