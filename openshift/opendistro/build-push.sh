#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null
source $SCRIPT_DIR/common.sh

$SUDO docker build -t $REGISTRY/$PROJECT_NAMESPACE/es-app -f docker/Dockerfile-es docker
$SUDO docker build -t $REGISTRY/$PROJECT_NAMESPACE/kibana-app -f docker/Dockerfile-kibana docker
$SUDO docker push $REGISTRY/$PROJECT_NAMESPACE/es-app
$SUDO docker push $REGISTRY/$PROJECT_NAMESPACE/kibana-app