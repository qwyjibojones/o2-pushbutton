# Download Container Dependencies

We are going to use a registry to store as a cache all dependencies required to install openshift 3.11

We will first create a directory for our cache.  This directory can be anywhere that you can mount to your local docker registry:

`mkdir /data/docker-registry-data`

We will next run a local registry as a docker container:

`docker run -d   -p 5000:5000   --restart=always   --name registry   -v /data/docker-registry-data:/var/lib/registry   registry:2`

This will mount the directory /data/docker-registry-data to the container /var/lib/registry.

You can use this shell script to download the images and push to  your local registry:

```bash
DEFAULT_ITEMS="\
openshift/origin-deployer:v3.11 \
openshift/origin-pod:v3.11.0 \
openshift/origin-node:v3.11 \
openshift/origin-control-plane:v3.11 \
openshift/origin-haproxy-router:v3.11 \
openshift/origin-pod:v3.11 \
openshift/origin-template-service-broker:v3.11 \
openshift/origin-docker-registry:v3.11 \
openshift/origin-console:v3.11 \
openshift/origin-service-catalog:v3.11 \
openshift/origin-web-console:v3.11 \
openshift/origin-metrics-server:v3.11 \
openshift/origin-metrics-heapster:v3.11 \
openshift/origin-metrics-schema-installer:v3.11 \
openshift/oauth-proxy:v1.1.0 \
openshift/prometheus-alertmanager:v0.15.2 \
openshift/prometheus-node-exporter:v0.16.0 \
openshift/prometheus:v2.3.2 \
grafana/grafana:5.2.1 \
cockpit/kubernetes:latest
"
QUAY_ITEMS="\
coreos/cluster-monitoring-operator:v0.1.1 \
coreos/prometheus-config-reloader:v0.23.2 \
coreos/prometheus-operator:v0.23.2 \
coreos/kube-rbac-proxy:v0.3.1 \
coreos/etcd:v3.2.22 \
coreos/kube-state-metrics:v1.3.1 \
coreos/configmap-reload:v0.0.1 \
"

for x in $DEFAULT_ITEMS ; do
  TARGET=localhost:5000/$x
  docker pull $x
  docker tag $x $TARGET
  docker push $TARGET
  docker rmi -f $TARGET
  docker rmi -f $x
done

for x in $QUAY_ITEMS ; do
  TARGET=localhost:5000/$x
  SOURCE=quay.io/$x
  docker pull $SOURCE
  docker tag $SOURCE $TARGET
  docker push $TARGET
  docker rmi -f $TARGET
  docker rmi -f $SOURCE
done
```

Now you can tar up your data directory and take it to a disconnected location.

```bash
cd /data/
tar cvfz docker-registry-data.tgz docker-registry-data
```

The only caveat is that you must bring your docker registry container as a separate tgz and then make sure you have the docker client installed on your disconnected machine.  Go to any directory copy the registry image to a registry.tgz

```bash
docker save registry:2 > registry.tgz
```
