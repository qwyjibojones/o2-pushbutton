# OMAR Builder Package

## Welcome to the One-Stop Shop for all your static O2 Deployments

### Purpose
This O2 builder package serves as a static copy of the state/configuration of an O2 deployment. Using this package you can redeploy this same version/configuration of O2 to any OpenShift cluster.

### File Breakdown

-   omar-deploy-package
    -   configmaps - folder of whatever Application Spring config files were used in the original deployment
    -   python - folder containing python deployment scripts
    -   templates - folder of whatever template files were used in the original deployment
    -   deployConfig.yml - the deployConfig.yml used to configure the original O2 deployment
    -   run.sh - the script to run to redeploy the original O2 deployment

### Requirements

-   For any Deployment
    -   An OpenShift cluster must already be set up and functioning properly
    -   The following Environment Variables must be set on whatever machine is running the `deploy-app.py` script
        -   OPENSHIFT_USERNAME - Username for logging into the OpenShift cluster
        -   OPENSHIFT_PASSWORD - Password for logging into the OpenShift cluster
        -   DOCKER_REGISTRY_PASSWORD - Password for the docker registry specified in your deployConfig.yml

### Usage

To redeploy this package version of O2 simply run `./run.sh <OpenShift-Cluster-Endpoint>`, where `<OpenShift-Cluster-Endpoint>` is the url of the OpenShift cluster you would like to deploy this version of O2 on.
