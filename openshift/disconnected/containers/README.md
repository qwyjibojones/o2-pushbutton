# Containers

We have included three docker files for containers you will be needing to bundle so we can serve up the OpenShift container dependencies.

* ansible
* httpd
* registry

Although the registry Dockerfile is no more than a pointer to the docker hub registry:2 location, we supplied the docker file for completeness.  We will first build the 3 docker images and tgz them [build-images.sh](./bundle-images.sh) and [bundle-images.sh](./bundle-images.sh):

```bash
./build-images.sh
./bundle-images.sh <optional destination>
```

where:

* **optional destination** is a output location for the bundled images for ansible, httpd, and registry.  Note the output must have a trailing slash. for example: `./bundle-images.sh /data/disconnected/`.  If this is left off then it will output to the current directory

We should now have the **ansible**, **httpd**, and the **registry** images in our local docker and we are ready to move on to the downloading of the dependencies for OpenShift

## Download Container Dependencies

We are going to use a registry we just built and downloaded to store our OpenShift 3.11 dependencies.

We will first create a directory for our cache.  This directory can be anywhere that you can mount to your local docker registry:

`mkdir /data/disconnected/docker-registry-data`

We will next run a local registry as a docker container:

`docker run -d   -p 5000:5000   --restart=always   --name registry   -v /data/disconnected/docker-registry-data:/var/lib/registry   registry`

This will mount the directory /data/docker-registry-data to the container /var/lib/registry.

You can use this shell script to download the images and push to your local registry [pull-okd-311-images](./pull-okd-311-images.sh):

Now you can tar up your data directory and take it to a disconnected location. Assuming you have the registry created in /data/docker-registry-data

```bash
cd /data/
tar cvfz docker-registry-data.tgz docker-registry-data
```

The only caveat is that you must bring your docker registry container as a separate tgz and then make sure you have the docker client installed on your disconnected machine.  

