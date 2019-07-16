# OMAR OPENSHIFT TEMPLATES

A collection of templates for all services and infrastructure needed for an OMAR/OpenShift Deployment.

The individual templates are _not_ intended to be loaded directly from neither the oc CLI nor the openshift console, as they refer to parameters and other boiler-plate items defined in a separate JSON template (`omar-common.json`). If needed, a usable template can be generated via the `generate-template.sh` script in the parent directory. Usage:

`</path/to/script/generate-template.sh <service-name>`

This will create a file in the current working directory called `<service-name>-template.json`.

Note that this will generate a template that includes the parameters list containing the same default values found in `omar-common.json` and `<service-name>.json`. You will still need to override those parameters, or edit the template, when deploying to openshift using the generated template.
