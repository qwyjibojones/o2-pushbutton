import logging
import os


def report_status(name, process):
    output, error = process.communicate()
    return_code = process.returncode
    if return_code == 0:
        logging.info('%s: Success!' % name)
        if len(output) > 0:
            logging.debug('stdout: %s' % output)
        if len(error) > 0:
            logging.debug('stderr: %s' % error)
    else:
        logging.error('!!!!! Failure with object: %s !!!!!' % name)
        if len(output) > 0:
            logging.warning('stdout: %s' % output)
        if len(error) > 0:
            logging.warning('stderr: %s' % error)

    return return_code


def get_template_path(app_name, app_params, template_dir):
    if template_dir is None:
        raise Exception('Template dir must be specified if deploying from templates')

    if 'template_file' not in app_params:
        raise Exception('Template file not specified for app %s' % app_name)

    full_template_path = os.path.join(template_dir, app_params['template_file'])
    if not os.path.isfile(full_template_path):
        raise Exception('Template file at %s does not exist or is not a file' % full_template_path)

    return full_template_path


def get_fromfile_path(app_name, app_params, configmap_dir):
    if configmap_dir is None:
        raise Exception('Configmap dir must be specified if deploying config maps from files')

    if 'from-file' not in app_params:
        raise Exception('Fromfile not specified for app %s' % app_name)

    full_configmap_path = os.path.join(configmap_dir, app_params['from-file'])
    if not os.path.exists(full_configmap_path):
        raise Exception('Configmap path at %s does not exist' % full_configmap_path)

    return full_configmap_path
