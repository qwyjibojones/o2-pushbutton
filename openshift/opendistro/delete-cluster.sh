#!/bin/bash
oc delete statefulset es-cluster
oc delete svc kibana elasticsearch
oc delete dc kibana
oc delete dc omar-web-proxy-app
oc delete configmap web-proxy-certs
oc delete configmap web-proxy-conf
oc delete service omar-web-proxy-app
oc delete route route-kibana-target
oc delete daemonset filebeat-es-cluster
oc delete configmap filebeat-prospectors
oc delete configmap filebeat-config
oc delete clusterrolebindings filebeat-es-cluster
oc delete clusterrole filebeat-es-cluster
oc delete serviceaccount filebeat-es-cluster
oc adm policy remove-scc-from-user privileged system:serviceaccount:es-stack:filebeat-es-cluster
