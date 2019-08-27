#!/bin/bash
DESTINATION_DIR=$1
ALL_OPTION=$2


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
echo $SCRIPT_DIR/docker-run.sh os-sync "rpmbuild -bb --nocheck openvswitch-2.9.2/rhel/openvswitch-fedora.spec"
$SCRIPT_DIR/docker-run.sh os-sync "rpmbuild -bb --nocheck openvswitch-2.9.2/rhel/openvswitch-fedora.spec"
mkdir extras
mv rpmbuild/RPMS/* extras/
rm -rf rpmbuild
rm -f openvswitch*
$SCRIPT_DIR/docker-run.sh os-sync "reposync -n -r centos-openshift-origin311"
$SCRIPT_DIR/docker-run.sh os-sync "reposync -n -r centos-ansible26"

if [ "${ALL_OPTION}" == "all" ] ; then
  $SCRIPT_DIR/docker-run.sh os-sync "reposync -n -r updates"
  $SCRIPT_DIR/docker-run.sh os-sync "reposync -n -r extras"
  $SCRIPT_DIR/docker-run.sh os-sync "reposync -n -r base"
fi

#
# We will  reate a repo for everyone if needed
#
$SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames ."

#
# Now create repo database for individual Repos
#

if [ -d "./centos-openshift-origin311" ] ; then
   $SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames centos-openshift-origin311"
fi

if [ -d "./updates" ] ; then
   $SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames updates"
fi

if [ -d "./base" ] ; then
   $SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames base"
fi

if [ -d "./extras" ] ; then
   $SCRIPT_DIR/docker-run.sh os-sync "createrepo --simple-md-filenames extras"
fi
popd