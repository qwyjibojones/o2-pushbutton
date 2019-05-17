#!/bin/bash
DESTINATION_DIR=$1

pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
export SCRIPT_DIR=`pwd -P`
popd >/dev/null

if [ "$DESTINATION_DIR" == "" ] ; then
  echo "You must supply a destination directory for the RPMS to be synchronized to."
  echo "Example: $0 /data/rpms"
  exit 1
fi
mkdir -p $DESTINATION_DIR

pushd $DESTINATION_DIR
$SCRIPT_DIR/docker-run.sh os-sync "reposync -n -r centos-openshift-origin311"
$SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames centos-openshift-origin311"
popd