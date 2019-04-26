#!/bin/bash
pushd `dirname ${BASH_SOURCE[0]}` >/dev/null
SCRIPT_DIR=`pwd -P`
popd >/dev/null

source $SCRIPT_DIR/common.sh


function usage {
  echo "Usage: $0 [options]"
  echo " options:"
  echo "     --help Display this help"
  echo "     --replicas Define the number of nodes in the cluster"
  echo "     --min-master-nodes Define the number of nodes in the cluster"
  echo "     --mem-size Mem size formatted in JAVA: Example 512m for 512 megabytes"
  echo "                or 2g for 2 gigs"
  echo "     --es-image Is the source image stream to pull from "
  echo "                example: docker-registry.default.svc:5000/es-stack/es-app:latest"
  echo "     --storage-size Formated in Openshift form of Storage sizes"
  echo "                10Gi is ten gigs or 1Ti is one terrabyte"
  echo "     --storage-class-name Specify the class name to use for the dynamic provisioning"
  echo "                          For aws you can specify gp2.   For glusterfs you can specify"
  echo "                          glusterfs-dynamic and if you installed the norep for 'No Replicatioun'"
  echo "                          you can use the value glusterfs-dynamic-norep"
  echo "     --project-namespace Give the namespace you wish to push the images to"
  echo ""
  echo ""
  echo "Example:"
  echo "     $0 --replicas 3 --storage-class-name glusterfs-dynamic-norep --storage-size 10Gi --mem-size 1g"
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
    --replicas)
    ES_CLUSTER_REPLICAS=$2
    shift
    shift
    ;; 
    --mem-size)
    ES_CLUSTER_MEM_SIZE=$2
    shift
    shift 
    ;;
    --es-image)
    ES_IMAGE=$2
    shift
    shift 
    ;;
    --min-master-nodes)
    ES_CLUSTER_MIN_MASTER_NODES=$2
    shift
    shift
    ;;
    --storage-size)
    ES_CLUSTER_STORAGE_SIZE="$2"
    shift
    shift
    ;;
    --storage-class-name)
    STORAGE_CLASS_NAME="$2"
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
if (( $ES_CLUSTER_MIN_MASTER_NODES > $ES_CLUSTER_REPLICAS )) ; then
    echo "The minimum number of master nodes must be less than "
    echo "or equal to the total number of replicas."

    exit 1
fi
ES_CLUSTER_LOCATIONS=
for ((i=0; i<$ES_CLUSTER_REPLICAS; ++i ))
do
  if [ "$ES_CLUSTER_LOCATIONS" == "" ] ; then
    ES_CLUSTER_LOCATIONS="es-cluster-$i.elasticsearch"
  else
    ES_CLUSTER_LOCATIONS="$ES_CLUSTER_LOCATIONS,es-cluster-$i.elasticsearch"
  fi
done

if [[ $ES_CLUSTER_STORAGE_SIZE != *"Gi" && $ES_CLUSTER_STORAGE_SIZE != *"Ti" ]] ; then
  echo "Storage size size must end with Ti for Terrabyte or Gi for gigabyte"
  exit 1
fi
if [[ $ES_CLUSTER_MEM_SIZE != *"m" && $ES_CLUSTER_MEM_SIZE != *"g" ]] ; then
  echo "Memory size size must end with m for megabyte or g for gigabyte"
  exit 1
fi
ES_YAML=$(loadfile ${TEMPLATE_DIR}es-app.yml)
ES_YAML=${ES_YAML//MEM_SIZE/$ES_CLUSTER_MEM_SIZE}
ES_YAML=${ES_YAML//CLUSTER_LOCATIONS/"$ES_CLUSTER_LOCATIONS"}
ES_YAML=${ES_YAML//MIN_MASTER_NODES/"$ES_CLUSTER_MIN_MASTER_NODES"}
ES_YAML=${ES_YAML//ES_IMAGE/"$ES_IMAGE"}
ES_YAML=${ES_YAML//ES_REPLICAS/"$ES_CLUSTER_REPLICAS"}
ES_YAML=${ES_YAML//STORAGE_SIZE/"$ES_CLUSTER_STORAGE_SIZE"}
ES_YAML=${ES_YAML//STORAGE_CLASS_NAME/"$STORAGE_CLASS_NAME"}

echo "$ES_YAML" > $SCRIPT_DIR/yaml/es-app.yml

oc create -f yaml/es-app-svc.yml
oc create -f yaml/es-app.yml