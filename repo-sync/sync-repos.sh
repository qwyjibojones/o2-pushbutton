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
mkdir -p rpmbuild/SOURCES
wget -q http://openvswitch.org/releases/openvswitch-2.9.2.tar.gz -O openvswitch-2.9.2.tar.gz
cp openvswitch-2.9.2.tar.gz rpmbuild/SOURCES/
tar xfz openvswitch-2.9.2.tar.gz;
$SCRIPT_DIR/docker-run.sh os-sync "rpmbuild -bb --nocheck openvswitch-2.9.2/rhel/openvswitch-fedora.spec"
mkdir extras
mv rpmbuild/RPMS/* extras/
rm -rf rpmbuild
rm -f openvswitch*
$SCRIPT_DIR/docker-run.sh os-sync "reposync -n -r centos-openshift-origin311"
$SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames centos-openshift-origin311"
$SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames extras"
popd