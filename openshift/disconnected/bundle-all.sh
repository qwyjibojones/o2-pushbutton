#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
BUNDLE_ALL_SCRIPT_DIR=`pwd -P`
popd >/dev/null

DESTINATION_DIR=$1

if [ "${DESTINATION_DIR}" == "" ] ; then
   DESTINATION_DIR="/data/disconnected"
fi

if [ ! -d "$DESTINATION_DIR" ] ; then
  echo "Directory ${DESTINATION_DIR} does not exist.  Creating directory..."
  mkdir -p $DESTINATION_DIR
fi

echo "Checking out openshift-ansible"
pushd ${DESTINATION_DIR}
git clone https://github.com/openshift/openshift-ansible.git
cd openshift-ansible
git checkout release-3.11
popd >/dev/null

echo "Building images......."
${BUNDLE_ALL_SCRIPT_DIR}/containers/build-images.sh
echo "Bundling images......."
${BUNDLE_ALL_SCRIPT_DIR}/containers/bundle-images.sh ${DESTINATION_DIR}

echo "Removing services............."
echo ${BUNDLE_ALL_SCRIPT_DIR}/remove-services.sh
${BUNDLE_ALL_SCRIPT_DIR}/remove-services.sh
mkdir -p ${DESTINATION_DIR}/registry
pushd ${DESTINATION_DIR}

echo "Copying service scripts.............."
cp ${BUNDLE_ALL_SCRIPT_DIR}/run-ansible.sh ${DESTINATION_DIR}/
cp ${BUNDLE_ALL_SCRIPT_DIR}/remove-services.sh ${DESTINATION_DIR}/
cp ${BUNDLE_ALL_SCRIPT_DIR}/reverse-proxy.conf ${DESTINATION_DIR}/
cp ${BUNDLE_ALL_SCRIPT_DIR}/run-services.sh ${DESTINATION_DIR}/
cp -R ${BUNDLE_ALL_SCRIPT_DIR}/server-certs ${DESTINATION_DIR}/
chmod +x ${BUNDLE_ALL_SCRIPT_DIR}/*.sh

echo "Starting registry services............."
pushd ${DESTINATION_DIR}
./run-services.sh .
popd > /dev/null

echo "Pulling all images required for installation and putting them in a local registry...."
${BUNDLE_ALL_SCRIPT_DIR}/containers/pull-okd-311-images.sh ${DESTINATION_DIR}

echo "Bundle up the registry directory........"
${BUNDLE_ALL_SCRIPT_DIR}/containers/bundle-okd-311-images.sh ${DESTINATION_DIR}


echo "Finished bundling dependencies.  You can now tar up the ${DESTINATION_DIR} for delivery"