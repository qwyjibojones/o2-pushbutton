# Installation steps

This README is a top level readme that just shows the order in which you should install the OpenShift environment.

## Disconnected Installation

If this is a disconnected installation you must bring in all necessary dependencies.

* Containers and RPMs needed [Disconnected README](./disconnected/README.md)


## Order of installation

* We must first configure an OpenShift environment.  
  - **Bare-metal** If you do not have a cloud environment then you will need to do a bare-metal installation.  For bare-metal installation please see the [README.md](./bare-metal/README.md) under the bare-metal directory for configuring openshift manually.
* Next, configure and install ElasticSearch Opendistro found under the opendistro drectory.  Please refer to the [README.md](./opendistro/README.md) under the opendistro directory.  
