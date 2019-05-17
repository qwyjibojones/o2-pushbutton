#!/bin/bash
SOURCE_DIR=$1

if [ "$SOURCE_DIR" == "" ] ; then
   SOURCE_DIR="/data/docker-registry-data"
fi
pushd /data/
tar cvfz docker-registry-data.tgz docker-registry-data
popd