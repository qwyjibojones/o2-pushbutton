#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
BUILD_IMAGES_SCRIPT_DIR=`pwd -P`
popd >/dev/null

docker build -t ansible:latest -f $BUILD_IMAGES_SCRIPT_DIR/ansible/Dockerfile $BUILD_IMAGES_SCRIPT_DIR/ansible
docker build -t httpd:latest -f $BUILD_IMAGES_SCRIPT_DIR/httpd/Dockerfile $BUILD_IMAGES_SCRIPT_DIR/httpd
docker pull registry:latest
