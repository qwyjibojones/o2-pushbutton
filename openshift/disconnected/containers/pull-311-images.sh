#!/bin/bash

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