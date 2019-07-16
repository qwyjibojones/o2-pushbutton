# O2 Pushbutton Openshift Deployment

## Welcome to the One-Stop Shop for all your O2 Deployment needs

### Purpose
This part of the o2-pushbutton repository houses an easy-to-use set of python scripts for easily deploying or redeploying an O2 instance.

### File Breakdown

 - `Jenkinsfile` - Used for running the deployment script through a Jenkins pipeline
 - `run.sh/build-omar-deploy-package.sh` - Used for creating a static deliverable of the deployed O2 instance
 - `python/` - Contains all the python scripts needed for the main deploy-app.py script
 - `templates` - Contains all template files for a given O2 deployment

### Requirements

-   For any Deployment
    -   An Openshift cluster must already be set up and functioning properly
    -   The following Environment Variables must be set on whatever machine is running the `deploy-app.py` script
        -   OPENSHIFT_USERNAME - Username for logging into the Openshift cluster
        -   OPENSHIFT_PASSWORD - Password for logging into the Openshift cluster
        -   DOCKER_REGISTRY_PASSWORD - Password for the docker registry specified in your deploymentConfig.yml
    -   The machine running the script must have direct access to the following things
        -   deploymentConfig.yml - This is the main deployment configuration file that holds all deployment variables and the listing of all services desired to be deployed (a templated example can be found in the repo linked above)
        -   Template Directory - This directory holds all .json templates for all apps that are desired to be deployed to openshift
        -   ConfigMap Directory - This directory holds all Application Spring config files used for the creation of any ConfigMaps that are desired in the deployment
-   Whole Suite Deployment
    -   There must be a default project from which Openshift can create the new project from
-   Single Service Deployment  
    -   The project the service is to be deployed in (specified in deploymentConfig.yml) must already exist unless the service being deployed is the project itself

### Usage
After cloning the pushbutton repo, navigate to the `python` directory. Below are a list of the different commands you can run.

-   Whole Suite Deployment
`python deploy-app.py -t <path-to-template-dir> -c <path-to-deploymentConfig.yml> -m <path-to-configmap-dir> -o <openshift-console-endpoint> --remove --loglevel debug --all DOCKER_REGISTRY_PASSWORD=${DOCKER_REGISTRY_PASSWORD}`
-   Single Service Deployment
`python deploy-app.py -t <path-to-template-dir> -c <path-to-deploymentConfig.yml> -m <path-to-configmap-dir> -o <openshift-console-endpoint> --remove --loglevel debug --service <name-of-app> DOCKER_REGISTRY_PASSWORD=${DOCKER_REGISTRY_PASSWORD}`

### deploymentConfig.yml
The deploymentConfig.yml is the main configuration for the deployment suite. You can view a sample for a template deploymentConfig.yml in this directory.

For the deploymentConfig.yml to be valid all environment variables required for your deployment must be specified under the `defaults` dictionary. Then all objects/apps must be listed under the `apps` dictionary. The script will build all object listed under `apps` in phases. Phases are separated by being separate lists of objects in `apps` section. A phase will not be built until all phases previous are done building.

All objects under the `apps` section must have at least one of the following specifications

 - Spec 1
	 - `type` - The type of object you want Openshift to create (i.e. configmap)
	 - `from-file` - Place where files for the configmap are located relative to the `path-to-configmap-dir` passed into the script
 - Spec 2
	 - `template_file` - Location of the template file for the object to be created relative to the `path-to-template-dir` passed into the script