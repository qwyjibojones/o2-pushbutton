import yaml
import sys
import argparse


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('configfile', help='The config file to parse')
    parser.add_argument('service', help='The service to get the parameters for')
    parser.add_argument('-k', '--key', required=False, help='A single key to return the value of')

    parsed_args = parser.parse_args(args)

    params = get_params_for_service(config_file=parsed_args.configfile, service_name=parsed_args.service)
    if parsed_args.key is None:
        print(yaml.dump(params, default_flow_style=False))
    else:
        print(params.get(parsed_args.key, None))


def load_deployment_config(config_file):
    return yaml.load(open(config_file).read())


# Convert overrides from a list of key=value pairs to a dictionary
def convert_overrides_to_dict(overrides):
    overrides_dict = {}
    for item in overrides:
        split_item = item.split('=', 1)
        if len(split_item) != 2:
            raise Exception('All overrides must be of the form key=value. The offender: %s' % item)
        key = split_item[0]
        value = split_item[1]
        overrides_dict[key] = value
    return overrides_dict


def get_defaults_from_config(loaded_config):
    return loaded_config['defaults']


def get_phases_from_config(loaded_config):
    return loaded_config['phases']


def get_simplified_phases_from_config(loaded_config):
    phases = [phase.keys() for phase in get_phases_from_config(loaded_config)]
    return phases


def generate_app_configs(loaded_config, overrides=[]):
    all_app_configs = {}
    for phase in get_phases_from_config(loaded_config):
        for app_name, app_params in phase.iteritems():
            params = generate_params_for_app(get_defaults_from_config(loaded_config),
                                             app_params,
                                             convert_overrides_to_dict(overrides))
            all_app_configs[app_name] = params

    return all_app_configs


def generate_params_for_app(default_params, app_params, overrides):
    params = {}
    params.update(default_params)
    params.update(app_params)
    params.update(overrides)
    return params


# Get the final parameters for a service after taking defaults, app-specific configs, and overrides into account
def get_params_for_service(config_file, service_name, overrides=[]):
    overrides_dict = convert_overrides_to_dict(overrides)
    loaded_config = load_deployment_config(config_file)
    params = loaded_config['defaults']
    for phase in loaded_config['phases']:
        if service_name in phase:
            params.update(phase[service_name])
            params.update(overrides_dict)
            return params
    raise Exception('No service named \'%s\' found in %s' % (service_name, config_file))


def get_namespace(config_file):
    loaded_config = load_deployment_config(config_file)
    if 'meta' in loaded_config:
        return loaded_config['meta'].get('namespace')


def get_deployment_phases(config_file):
    loaded_config = load_deployment_config(config_file)
    phases = [phase.keys() for phase in loaded_config['phases']]
    return phases


if __name__ == '__main__':
    main(sys.argv[1:])
