import argparse
import sys
import logging
import os

import parse_deploy_sequence
import openshift
import helpers

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument('-c', '--config-file', required=True, help='The deployConfig yml file to use')
argument_parser.add_argument('-o', '--openshift-url', required=True, help='The url of the openshift instance to deploy to')
argument_parser.add_argument('-f', '--folder-dir', required=True, help='The directory where the openshift configmap files are located')
argument_parser.add_argument('--all', required=False, action='store_true', help='Deploy all configmaps defined in the deployConfig file')
argument_parser.add_argument('-m', '--map', required=False, help='Deploy the provided map. Overridden by the \'--all\' flag')
argument_parser.add_argument('--remove', required=False, action='store_true', help='Remove existing objects first')
argument_parser.add_argument('--no-deploy', required=False, action='store_true', help='Avoid deploying apps, just remove them')
argument_parser.add_argument('--loglevel', default='INFO', type=str.upper, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL'], help='The log level to use')


def process_all(config_file, folder_dir, remove_app, deploy_app):
    configmaps = parse_deploy_sequence.get_configmaps(config_file)

    for key, value in configmaps.iteritems():
        app_name = key
        process_map(config_file=config_file,
                    folder_dir=folder_dir,
                    app_name=app_name,
                    remove_app=remove_app,
                    deploy_app=deploy_app)


def process_map(config_file, folder_dir, app_name, remove_app, deploy_app):
    logging.info('Deploying configmap: %s' % app_name)

    configmap = parse_deploy_sequence.get_configmaps(config_file=config_file)[app_name]

    fromfile = configmap['from-file']
    full_fromfile_path = os.path.join(folder_dir, fromfile)
    if not os.path.exists(full_fromfile_path):
        raise Exception('Fromfile path at %s does not exist' % full_fromfile_path)

    if remove_app:
        logging.info('Removing existing configmap %s' % app_name)
        openshift.remove_configmap(app_name)

    if deploy_app:
        logging.info('Adding configmap %s' % app_name)
        deploy_process = openshift.create_configmap(name=app_name,
                                                    fromfile=full_fromfile_path)
        helpers.report_status(name=app_name,
                              process=deploy_process)


def get_template_path(app_name, template_dir, app_params):

    if 'from-file' not in app_params:
        raise Exception('Template file not specified for app %s' % app_name)

    full_template_path = os.path.join(template_dir, app_params['template_file'])
    if not os.path.isfile(full_template_path):
        raise Exception('Template file at %s does not exist or is not a file' % full_template_path)\

    return full_template_path


def main(args):
    parsed_args = argument_parser.parse_args(args)
    logging.info('Using config file: %s\nand folder dir:%s' % (parsed_args.config_file, parsed_args.folder_dir))

    openshift.login(openshift_url=parsed_args.openshift_url,
                    username=os.getenv('OPENSHIFT_USERNAME'),
                    password=os.getenv('OPENSHIFT_PASSWORD'))

    if parsed_args.all:
        process_all(config_file=parsed_args.config_file,
                    folder_dir=parsed_args.folder_dir,
                    remove_app=parsed_args.remove,
                    deploy_app=not parsed_args.no_deploy,)
    else:
        process_map(config_file=parsed_args.config_file,
                    folder_dir=parsed_args.folder_dir,
                    app_name=parsed_args.map,
                    remove_app=parsed_args.remove,
                    deploy_app= not parsed_args.no_deploy)


if __name__ == '__main__':
    main(sys.argv[1:])
