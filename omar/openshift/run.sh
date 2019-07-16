#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then
  echo "Please provide an openshift url as a parameter" 1>&2
  exit 1
fi

if [[ -z $OPENSHIFT_USERNAME || -z $OPENSHIFT_PASSWORD || -z $DOCKER_REGISTRY_PASSWORD ]]; then
  echo "Please provide the openshift username and password, and the external docker registry password in the following environment variables:
    OPENSHIFT_USERNAME
    OPENSHIFT_PASSWORD
    DOCKER_REGISTRY_PASSWORD"
  exit 2
fi

OPENSHIFT_URL="${1}"

python ./python/deploy-app.py -t ./templates -c ./deployConfig.yml -m ./configmaps -o "${OPENSHIFT_URL}" --remove --loglevel info --all DOCKER_REGISTRY_PASSWORD="${DOCKER_REGISTRY_PASSWORD}"
