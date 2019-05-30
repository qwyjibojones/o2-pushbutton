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
    --es-username)
    ES_USERNAME=$2
    shift
    shift
    ;;
    --es-password)
    ES_PASSWORD=$2
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
FILEBEAT_YAML=$(loadfile ${TEMPLATE_DIR}filebeat.yml)
FILEBEAT_YAML=${FILEBEAT_YAML/PROJECT_NAMESPACE/"$PROJECT_NAMESPACE"}
FILEBEAT_YAML=${FILEBEAT_YAML/ES_USERNAME/"$ES_USERNAME"}
FILEBEAT_YAML=${FILEBEAT_YAML/ES_PASSWORD/"$ES_PASSWORD"}
echo "$FILEBEAT_YAML" > $SCRIPT_DIR/yaml/filebeat.yml

oc create -f $SCRIPT_DIR/logging/filebeat.yml
