#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null
source $SCRIPT_DIR/common.sh

$SUDO docker login -u unused -p $(oc whoami -t) $REGISTRY_URL
