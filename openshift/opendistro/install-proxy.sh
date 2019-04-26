#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null

source $SCRIPT_DIR/common.sh
HOSTNAME="os-kibana.ossim.io"
CA_CERTS=$(loadfile $SCRIPT_DIR/proxy/web-proxy-certs/ca.crt)
SERVER_PRIVATE=$(loadfile $SCRIPT_DIR/proxy/web-proxy-certs/server.key)
SERVER_PUB=$(loadfile $SCRIPT_DIR/proxy/web-proxy-certs/server.key)

POSITIONAL=()
while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
    --help)
    usage   
    shift
    exit 0
    ;; 
    --hostname)
    HOSTNAME=$2
    shift
    shift
    ;; 
    *)
    echo "Unknown option $1"
    exit 1
    shift
    ;;
  esac
done



if [ "$CA_CERTS" == "" ] ; then
   echo "$CA_CERTS is empty. Please add your root CA chain to the"
   exit 1
fi

if [ "$SERVER_PRIVATE" == "" ] ; then
   echo "$SERVER_PRIVATE is empty. Please add your private key in a PEM format with no password"
   exit 1
fi

if [ "$SERVER_PUB" == "" ] ; then
   echo "$SERVER_PUB is empty. Please add your public server key in a PEM format"
   exit 1
fi


oc create configmap web-proxy-certs --from-file=$SCRIPT_DIR/proxy/web-proxy-certs
oc create configmap web-proxy-conf --from-file=$SCRIPT_DIR/proxy/web-proxy-conf

oc create -f $SCRIPT_DIR/proxy/omar-web-proxy-svc.yml
oc create -f $SCRIPT_DIR/proxy/omar-web-proxy-app.yml

oc create route passthrough route-kibana-target --service omar-web-proxy-app --hostname=$HOSTNAME --port=443

oc rollout latest  dc/omar-web-proxy-app
