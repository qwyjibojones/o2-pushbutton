# O2 Pushbutton OpenShift Deployment

See the [Quickstart](#Quickstart) section for a full scale example installation of the entire O2 baseline.

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

## Quickstart

This is a quick start guide on installing the O2 distribution.  Before we do a full deploy we need to have two services start before all other services.  We will create two install deployments that will do the first two services and then a full install for all the other services.  For this guide we will assume the following:

- Openshift project name will be **omar-test**
- NFS name will be o2-nfs.private.ossim.io
- Domain will be ossim.io

For you distribution please modify any values in this Quickstart guide that pertains to your environment.  For example, you will probably have a different NFS endpoint than what these files will assume.

### Step 1

Please make sure the target project is created.

```bash
oc new-project omar-test
```

### Step 2

Pull down the initial scripts found in the o2-pushbutton repository.  We don't need everything in the repo but for now we will grab the entire repository.

```bash
mkdir o2-install
cd o2-install
git clone https://github.com/ossimlabs/o2-pushbutton
git clone git@github.com:Maxar-Corp/config-repo.git
mkdir pre-install
mkdir full-install
```

### Step 3

Create a file pre-install/deployConfig.yml and edit the contents to enable the **config** and **eureka** services for deployment.

For an example you can look at the template file called [TEMPLATE-deploymentConfig.yml](TEMPLATE-deploymentConfig.yml).

For convenience we have supplied a [preInstallDeploy.yml](quickstart/preInstallDeploy.yml) for an example of an O2 install of these services.

```bash
cp o2-pushbutton/omar/openshift/quickstart/preInstallDeploy.yml pre-install/deployConfig.yml
```

In whatever text editor you are familiar with edit **pre-install/deployConfig.yml** and modify the values for your environment

### Step 4

Execute the installation process for the two services.

```
python o2-pushbutton/omar/openshift/python/deploy-app.py -t o2-pushbutton/omar/openshift/templates -c quickstart/preInstallDeploy.yml -m config-repo/configmaps -o https://localhost:8443 --loglevel debug --all
```

### Step 5

Create a file pre-install/deployConfig.yml and edit the contents to enable the config and eureka services for deployment.

For an example you can look at the template file called [TEMPLATE-deploymentConfig.yml](TEMPLATE-deploymentConfig.yml).

For convenience we have supplied a [fullInstallDeploy.yml](quickstart/fullInstallDeploy.yml) for a complete example of an O2 install under the project omar-test.

```bash
cp o2-pushbutton/omar/openshift/quickstart/fullInstallDeploy.yml full-install/deployConfig.yml
```

In whatever text editor you are familiar with edit **full-install/deployConfig.yml** and modify the values for your environment

### Step 6

Execute the installation process for the rest of the services.

```
python o2-pushbutton/omar/openshift/python/deploy-app.py -t o2-pushbutton/omar/openshift/templates -c quickstart/fullInstallDeploy.yml -m config-repo/configmaps -o https://localhost:8443 --loglevel debug --all
```

### Step 7

Browse to the OpenShift cluster and watch the services come up under the omar-test project.

### Step 8

Browse to the https://<O2 URL ENDPOINT>/omar-ui

## Tips

In this section you will find some tips with some useful commands.

### Deleting PVs

When Deleting the project the PV's are not deleted for they are defined outside the project.  The PVC's are deleted but not the PVs.  To get a list of all the PVs in you can execute the command:

```bash
oc get pv
```

if your PVs were all postfixed with **test** then you can do something like this to modify the listing:

```bash
oc get pv | grep "\-test"
```

and will give you an output that might look something like this:

```text
basemap-test             75Gi       ROX            Retain           Bound      omar-test/basemap-test-pvc
ossim-data-test          1500Gi     RWX            Retain           Bound      omar-test/ossim-data-test-pvc
ossim-video-data-test    1500Gi     RWX            Retain           Bound      omar-test/ossim-video-data-test-pvc
web-proxy-crl-test       1Gi        RWX            Retain           Bound      omar-test/web-proxy-crl-test-pvc
```

After the project is deleted and the PVCs are gone then you can delete the PV:

```bash
   oc delete pv $(oc get pv | grep "\-test" | awk '{print $1}')
```
