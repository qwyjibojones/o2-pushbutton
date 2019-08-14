# Disconnected OpenShift 3.11 origin (Now OKD) Installation Dependencies

## Syncronizing Repos for Disconnected Installation

Step 1.: [Syncrhonize the RPMs](./repo-sync/README.md)
**Notes:** For disconnected installations of OpenShift 3.11 we need to synchronize RPM repos for the containers that will be running in the OpenShift environment.

Step 2.: [Download all Containers](./containers/README.md)
**Notes:** For disconnected installations of OpenShift 3.11 we need to download all images for the containers that will be running in the OpenShift environment. 

Step 3.: 
```bash
  cp server-certs /data/disconnected/
  cp reverse-proxy.conf /data/disconnected
```
**Notes:** These are self signed CERTS so we can proxy https.  Please copy the **/server-certs** directory to the working location.

## Load Dependencies

Somehow bring `/data/disconnected` and this repository to a disconnected location we need to run the proxy server which serves as a https proxy to the docker registry and also serves up the YUM repository that we just cached.

```bash
docker load -i registry.tgz
docker load -i httpd.tgz
docker load -i ansible.tgz
```

### Serve out dependencies

Once we have loaded the docker images into our docker we can now execute the run-services.  It will take an argument that is the working directory that serves at the root directory for the container registry cache, rpms, ... etc.

In this section we will now assume all dependencies will be extracted to a root working directory indicated by WORKING_DIRECTORY.  For example, let's assume we have extracted bundled all dependencies under a tgz call disconnected.tgz into the working directory giving us so far:

* **$WORKING_DIRECTORY/docker-registry-data**
* **$WORKING_DIRECTORY/rpms**
* **$WORKING_DIRECTORY/server-certs**
* **$WORKING_DIRECTORY/reverse-proxy.conf**

We can now serve these out via our local proxy **httpd** and our **registry** by running [run-services.sh](./run-services.sh).

`./run-services.sh <working directory>`


## NOTES TO INTEGRATE

### File Context Type

Changes context to allow directory and files to be accessed via a running container.  Needed for the registry

`sudo chcon -Rt svirt_sandbox_file_t <data-dir-to-mount>`

### Ports To Open

Open ports for our registry server:

```bash
firewall-cmd --zone-public --permanent --add-port=5000/tcp
firewall-cmd --zone=public --add-service=http
firewall-cmd --zone=public --add-service=https
firewall-cmd --reload
```

### SELINUX

Enable selinus for web access on the installer.

`sudo setsebool -P httpd_can_network_connect on`

### Enable IP Forwarding

Add IP forward to all nodes

`sudo vi /etc/sysctl.d/99-sysctl.conf`

then add the line

`net.ipv4.ip_forward = 1`

Then reload:

sudo systctl --load /etc/sysctl.d/99-sysctl.conf


# Testing docker registry:

curl -X GET https://localhost/v2/_catalog

list tags for a specific image listed in the catalog:

curl -X GET https://localhost/v2/<image-path-and-name>/tags/list




