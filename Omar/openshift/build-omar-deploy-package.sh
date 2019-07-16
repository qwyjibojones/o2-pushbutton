#!/usr/bin/env bash

CONFIG_REPO_NAME="$1"

mkdir omar-deploy-package

cp -r \
  o2-pushbutton/omar/openshift/run.sh \
  o2-pushbutton/omar/openshift/README.md \
  o2-pushbutton/omar/openshift/python \
  o2-pushbutton/omar/openshift/templates \
  ${CONFIG_REPO_NAME}/deployConfig.yml \
  ${CONFIG_REPO_NAME}/configmaps \
    omar-deploy-package

chmod a+x omar-deploy-package/run.sh
tar -czf omar-builder.tgz omar-deploy-package
