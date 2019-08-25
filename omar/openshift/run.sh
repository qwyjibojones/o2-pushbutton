#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then
  echo "Please provide an openshift url as a parameter" 1>&2
  exit 1
fi

if [[ -z $OPENSHIFT_USERNAME ]]; then
    read -p "Openshift Username: " OPENSHIFT_USERNAME
fi

if [[ -z $OPENSHIFT_PASSWORD ]]; then
    read -p "Openshift Password: " -s OPENSHIFT_PASSWORD
fi

export OPENSHIFT_USERNAME
export OPENSHIFT_PASSWORD

OPENSHIFT_URL="${1}"
shift

python ./python/deploy-app.py -t ./templates -c ./deployConfig.yml -m ./configmaps -o "${OPENSHIFT_URL}" --oc-location ./oc --remove --loglevel info --all --wait-for-pods --overrides "$@"
