#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null


function usage {
  echo "Usage: $0 [options]"
  echo " options:"
  echo "     --help Display this help"
  echo "     --project-namespace Give the namespace you wish to push the images to"
}

POSITIONAL=()
while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
    --project-namespace)
    PROJECT_NAMESPACE=$2
    shift
    shift
    ;;
    *)
    echo "Unknown option $1"
    exit 1
    shift
    ;;
  esac
done

source $SCRIPT_DIR/common.sh
oc adm policy add-scc-to-user privileged system:serviceaccount:$PROJECT_NAMESPACE:filebeat-es-cluster
oc create -f $SCRIPT_DIR/logging/filebeat.yml
