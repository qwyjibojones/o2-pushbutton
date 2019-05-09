# Download Container Dependencies

We are going to use a registry to store as a cache all dependencies required to install openshift 3.11

We will first create a directory for our cache.  This directory can be anywhere that you can mount to your local docker registry:

`mkdir /data/docker-registry-data`

We will next run a local registry as a docker container:

`docker run -d   -p 5000:5000   --restart=always   --name registry   -v /data/docker-registry-data:/var/lib/registry   registry:2`

This will mount the directory /data/docker-registry-data to the container /var/lib/registry.

You can use this shell script to download the images and push to your local registry [pull-311-images](./pull-311-images.sh):

Now you can tar up your data directory and take it to a disconnected location.

```bash
cd /data/
tar cvfz docker-registry-data.tgz docker-registry-data
```

The only caveat is that you must bring your docker registry container as a separate tgz and then make sure you have the docker client installed on your disconnected machine.  Go to any directory copy the registry image to a registry.tgz

```bash
docker save registry:2 > registry.tgz
```
