#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
BUNDLE_OKD_SCRIPT_DIR=`pwd -P`
popd >/dev/null
SOURCE_DIR=$1

if [ "${SOURCE_DIR}" == "" ] ; then
   echo "Please specify the location of your docker registry root directory...."
   exit 1  
fi
pushd ${SOURCE_DIR}
tar cvfz docker-registry-data.tgz registry
popd