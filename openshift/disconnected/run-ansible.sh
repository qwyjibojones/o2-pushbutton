#!/bin/bash
WORKING_DIRECTORY=$1
ANSIBLE_IMAGE_NAME=ansible
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
RUN_ANSIBLE_SCRIPT_DIR=`pwd -P`
popd >/dev/null

if [ "${WORKING_DIRECTORY}" == "" ] ; then
   echo "Working directory not specified.  Please specify working directory"
   echo "Usage: ${0} <working-directory>"
   exit 1
fi

docker run --rm --name ${ANSIBLE_IMAGE_NAME} -v $WORKING_DIRECTORY:/home/ansible ansible ${@:2}

