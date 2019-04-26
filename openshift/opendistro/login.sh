#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null
source $SCRIPT_DIR/common.sh

function usage {
  echo "Usage: $0 [options]"
  echo " options:"
  echo "     --help Display this help"
  echo "     --registry-url Give the full url for the registry: http://myregistry.foo.io"
  echo ""
  echo ""
  echo "Example:"
  echo "     $0 --registry myregistry.foo.io "
}


POSITIONAL=()
while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
    --help)
    usage   
    shift
    exit 0
    ;;
    --registry-url)
    REGISTRY_URL=$2
    REGISTRY=${REGISTRY_URL##*/}
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


$SUDO docker login -u unused -p $(oc whoami -t) $REGISTRY_URL
