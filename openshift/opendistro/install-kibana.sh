#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null

source $SCRIPT_DIR/common.sh

function usage {
  echo "Usage: $0 [options]"
  echo " options:"
  echo "     --help Display this help"
  echo "     --es-replicas This is the number of nodes defined in the"
  echo "                   elastic search cluster previously executed"
  echo "                   by the install-es.sh"
  echo "     --kibana-replicas This is the number of kibana replicas to set on startup"
  echo "     --es-image Is the source elasticsearch image stream to pull from "
  echo "                defaults to: docker-registry.default.svc:5000/es-stack/es-app:latest"
  echo "     --kibana-image Is the source kibana image stream to pull from "
  echo "                defaults to: docker-registry.default.svc:5000/es-stack/kibana-app:latest"
  echo "     --project-namespace Give the namespace you wish to push the images to"
  echo ""
  echo ""
  echo "Example:"
  echo "     ./install-kibana.sh --kibana-replicas 2 --es-replicas 6"
}

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
    --es-replicas)
    ES_CLUSTER_REPLICAS=$2
    shift
    shift
    ;; 
    --kibana-replicas)
    KIBANA_REPLICAS=$2
    shift
    shift
    ;; 
    --es-image)
    ES_IMAGE=$2
    shift
    shift 
    ;;
    --kibana-image)
    KIBANA_IMAGE=$2
    shift
    shift 
    ;;
    --project-namespace)
    PROJECT_NAMESPACE=$2
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

ES_CLUSTER_LOCATIONS=
for i in $(eval echo "{1..$ES_CLUSTER_REPLICAS}") ; do
  if [ "$ES_CLUSTER_LOCATIONS" == "" ] ; then
    ES_CLUSTER_LOCATIONS="es-cluster-$i.elasticsearch"
  else
    ES_CLUSTER_LOCATIONS="$ES_CLUSTER_LOCATIONS,es-cluster-$i.elasticsearch"
  fi
done
KIBANA_YAML=$(loadfile ${TEMPLATE_DIR}kibana-app.yml)
KIBANA_YAML=${KIBANA_YAML/KIBANA_REPLICAS/"$KIBANA_REPLICAS"}
KIBANA_YAML=${KIBANA_YAML/CLUSTER_LOCATIONS/"$ES_CLUSTER_LOCATIONS"}
KIBANA_YAML=${KIBANA_YAML/KIBANA_IMAGE/"$KIBANA_IMAGE"}
KIBANA_YAML=${KIBANA_YAML/ES_IMAGE/"$ES_IMAGE"}
echo "$KIBANA_YAML" > $SCRIPT_DIR/yaml/kibana-app.yml

oc create -f yaml/kibana-app-svc.yml
oc create -f yaml/kibana-app.yml
