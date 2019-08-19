#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
export SCRIPT_DIR=`pwd -P`
popd >/dev/null

DESTINATION_DIR=$1

#docker save ansible|gzip -c>${DESTINATION_DIR}ansible.tgz
docker save httpd|gzip -c>${DESTINATION_DIR}httpd.tgz
docker save registry|gzip -c>${DESTINATION_DIR}registry.tgz

