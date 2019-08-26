#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
export SCRIPT_DIR=`pwd -P`
popd >/dev/null

pushd $SCRIPT_DIR
#docker build -t ansible:latest -f $SCRIPT_DIR/ansible/Dockerfile $SCRIPT_DIR/ansible
docker build -t httpd:latest -f $SCRIPT_DIR/httpd/Dockerfile $SCRIPT_DIR/httpd
docker build -t registry -f $SCRIPT_DIR/../../../docker-registry/Dockerfile $SCRIPT_DIR/registry
popd
