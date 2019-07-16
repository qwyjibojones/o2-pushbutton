import subprocess
import tempfile
import logging
import yaml


def run_command(args, wait=False, log=True):
    if log:
        logging.debug('Running command: `%s`' % ' '.join(args))
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if wait:
        process.wait()

    return process


def login(openshift_url, username, password):
    login_process = run_command(['oc', 'login', openshift_url, '--username=%s' % username, '--password=%s' % password],
                                wait=True,
                                log=False)
    if login_process.returncode != 0:
        raise Exception('Invalid openshift credentials provided, unable to login')


def change_project(project_name):
    run_command(['oc', 'project', project_name], wait=True)


def write_temporary_file(input_data):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(input_data)
    tmp.close()
    return tmp.name


def remove_configmap(item_name):
    return run_command(['oc', 'delete', '--now', '--wait', 'configmap', item_name], wait=True)


def create_configmap(name, fromfile, namespace, wait=False):
    return run_command(['oc', 'create', 'configmap', name, '--from-file', fromfile, '--namespace', namespace], wait=wait)


def remove_objects_in_processed_template(processed_file, wait=True):
    return run_command(['oc', 'delete', '--now', '--wait', '-f', processed_file], wait)


def process_template(template_file, params):
    temp_params_file = write_temporary_file(yaml.dump(params, default_flow_style=False))
    command_args = ['oc', 'process', '-f', template_file, '--param-file', temp_params_file,
                    '--ignore-unknown-parameters']
    temp_processed_file = write_temporary_file(run_command(command_args, True).stdout.read())
    return temp_processed_file


def new_app(template_file, params, wait=False):
    temp_params_file = write_temporary_file(yaml.dump(params, default_flow_style=False))
    command_args = ['oc', 'new-app', '-f', template_file, '--param-file', temp_params_file, '--ignore-unknown-parameters']
    return run_command(command_args, wait)
