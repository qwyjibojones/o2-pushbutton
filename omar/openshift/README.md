# O2 Pushbutton OpenShift Deployment

## Welcome to the One-Stop Shop for all your O2 Deployment needs

### Purpose
This part of the o2-pushbutton repository houses an easy-to-use set of python scripts for quickly deploying or redeploying an O2 instance.

### File Breakdown

 - `Jenkinsfile` - Used for running the deployment script through a Jenkins pipeline
 - `run.sh/build-omar-deploy-package.sh` - Used for creating a static deliverable of the deployed O2 instance
 - `python/` - Contains all the python scripts needed for the main deploy-app.py script
 - `templates/` - Contains all template files for a given O2 deployment

### Requirements

-   For any Deployment
    -   An OpenShift cluster must already be set up and functioning properly
    -   The following Environment Variables must be set on whatever machine is running the `deploy-app.py` script
        -   OPENSHIFT_USERNAME - Username for logging into the OpenShift cluster
        -   OPENSHIFT_PASSWORD - Password for logging into the OpenShift cluster
        -   DOCKER_REGISTRY_PASSWORD - Password for the docker registry specified in your deployConfig.yml
    -   The machine running the script must have direct access to the following things
        -   deployConfig.yml - This is the main deployment configuration file that holds all deployment variables and the listing of all services desired to be deployed (a templated example can be found in the repo linked above)
        -   Template Directory - This directory holds all .json templates for any apps/objects that are desired to be deployed to OpenShift
        -   ConfigMap Directory - This directory holds all application config files used for the creation of any ConfigMaps that are desired in the deployment
-   Whole Suite Deployment
    -   There must be a default project from which OpenShift can create the new project from
-   Single Service Deployment  
    -   The project the service is to be deployed in (specified in deployConfig.yml) must already exist unless the service being deployed is the project itself

### Usage
After cloning the pushbutton repo, navigate to the `python` directory. Below are a list of the different commands you can run.

-   Whole Suite Deployment
`python deploy-app.py -t <path-to-template-dir> -c <path-to-deployConfig.yml> -m <path-to-configmap-dir> -o <openshift-console-endpoint> --remove --loglevel debug --all DOCKER_REGISTRY_PASSWORD=${DOCKER_REGISTRY_PASSWORD}`
-   Single Service Deployment
`python deploy-app.py -t <path-to-template-dir> -c <path-to-deployConfig.yml> -m <path-to-configmap-dir> -o <openshift-console-endpoint> --remove --loglevel debug --service <name-of-app> DOCKER_REGISTRY_PASSWORD=${DOCKER_REGISTRY_PASSWORD}`

### deployConfig.yml
The `deployConfig.yml` is the main configuration for the deployment suite. For a templated sample `deployConfig.yml` look in this directory under `TEMPLATE-deployConfig.yml`.

For the `deployConfig.yml` to be valid all environment variables required for your deployment must be specified under the `defaults` dictionary. Then all objects/apps must be listed under the `phases` dictionary. The script will build all object listed under `phases`. Since `phases` is a list of dictionaries, each phase is separated by being a separate entry in that list. A phase will not be built until all previous phases are done building.

All objects under the `phases` section must have at least one of the following specifications

 - Spec 1
	 - `type` - The type of object you want OpenShift to create (i.e. configmap). Currently, only configmap is treated differently from templates.
	 - `from-file` - Place where files for the configmaps are located relative to the `--configmap-dir` passed into the script
 - Spec 2
	 - `template_file` - Location of the template file for the object to be created relative to the `--template-dir` passed into the script

### OpenShift Object Creation Guidelines

As far as OpenShift object creation is concerned, we suggest grouping/creating objects with the following guidelines.
- **Project:**
For the overall project, we ***strongly suggest*** creating it on its own through a separate .json template and it ***must*** be the first object created (appearing first under `phases` in the `deployConfig.yml`). An example can be seen in `templates/infra/project.json`. Otherwise, the project must be created manually before any other apps are deployed.
- **PVs and PVCs:**
For PVs and PVCs we suggest creating them using the same .json template where the PVCs are listed before any PVs are listed. Examples of this can be seen in `templates/infra/persistent-volumes.json`
- **Registry Creds:**
We suggest defining any credentials used for your docker registry to be defined in the 	`deployConfig.yml` after the project and any PV/PVCs are defined. An example of the .json template can be found under `templates/secrets/registry-creds.json`
- **Routes:**
For routes, we suggest creating them as an object separate from everything else so that they can be updated, deployed, and removed separately. Examples of this can be seen in `templates/infra/routes.json`
- **ConfigMaps:**
For ConfigMaps, we suggest each ConfigMap having its own entry in the `deployConfig.yml` before any of the individual applications are listed
- **Services/deployments/pods:**
For these applications, we suggest each app have its own .json template and appear in the deployConfig.yml ***after*** the above objects. Examples can be seen in `templates/apps/*` and a sample template can be found in `templates/A-SAMPLE-TEMPLATE.json`

### omar-builder.tgz
Within this repository also exists a script called `build-omar-deploy-package.sh` which bundles all configuration files used for an O2 deployment and a `run.sh` which can then be run from any machine to deploy that version of the deployment configured in the same way to any OpenShift cluster. To use the `run.sh` simply untar the deployment package, cd into the new `omar-deployment-package` dir, and run `./run.sh <OpenShift-Cluster-Endpoint>`. This will deploy O2 with whatever configuration files were last used to the endpoint specified at runtime.

**NOTE:** The `build-omar-deploy-package.sh` bundles the files based off pathnames that exists when the Jenkins Pipeline file is run. So you will either need to edit the script slightly or make sure the pathnames for your own set of configuration files match that of the script. Also, using the `omar-build.tgz` has the same requirements as running the deployment scripts directly.