# Syncronizing Repos for Disconnected Installation

For disconnected installations we need to synchronize RPM repos and download all images for the containers that will be running in the OpenShift environment.  We have created a directory that called repo-sync that will manage synchronizing the RPMs required for the OpenShift Origin 3.11 installation.

* Synchronize RPMs [README.md](./repo-sync/README.md)
* Download all Images required for OpenShift origin 3.11 [README.md](./containers/README.md).

## Set up repo on Disconnected Host

```bash
cd /data/
tar cvfz docker-registry-data.tgz docker-registry-data
```

The only caveat is that you must bring your docker registry container as a separate tgz and then make sure you have the docker client installed on your disconnected machine.  Go to any directory copy the registry image to a registry.tgz

```bash
docker save registry:2 > registry.tgz
```
