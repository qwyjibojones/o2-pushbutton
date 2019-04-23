#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null

source $SCRIPT_DIR/common.sh
oc adm policy add-scc-to-user privileged system:serviceaccount:$PROJECT_NAMESPACE:filebeat-es-cluster
oc create -f $SCRIPT_DIR/logging/filebeat.yml
