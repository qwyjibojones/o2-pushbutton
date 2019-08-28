#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
BUNDLE_IMAGES_SCRIPT_DIR=`pwd -P`
popd >/dev/null

DESTINATION_DIR=$1

mkdir -p ${DESTINATION_DIR}/docker-images
docker save ansible|gzip -c>${DESTINATION_DIR}/docker-images/ansible.tgz
docker save httpd|gzip -c>${DESTINATION_DIR}/docker-images/httpd.tgz
docker save registry|gzip -c>${DESTINATION_DIR}/docker-images/registry.tgz

