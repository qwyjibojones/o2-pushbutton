#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
export SCRIPT_DIR=`pwd -P`
popd >/dev/null
pushd $SCRIPT_DIR
docker build -t os-sync .
popd