# Install Guide for Opendistro ElasticSearch Into OpenShift Environment

Prerequisite of ElasticSearch requires you to bump up the vm.max_map_count=262144. There is a file supplied in this repo found under the directory nod-config/99-es-stack.conf.  This file needs to be copied to all nodes in the cluster.  Example, lets assume that you have a DNS prefix of openshift-test-node-1.mysubdomain.io and you have 6 nodes in your cluster then:

```bash
for x in {1..6} ; do scp node-config/99-es-stack.conf openshift-test-node-$x.mysubdomain.io:/tmp/; ssh openshift-test-node-$x.mysubdomain.io "sudo cp /tmp/99-es-stack.conf /etc/sysctl.d/;sudo sysctl --system"; done;
```

We will assume the project namespace is es-stack and if you call it a different project then use that as the name space name for everything.

Login into openshift

``` bash
ssh <master node>
oc login
```

Create a new project called es-stack

``` bash
oc new-project es-stack
```

Now make sure you are in this directory where this README is located and execute the commands that follow to install the cluster

Next build the elasticsearch image and Kibana image

``` bash
./build-push.sh
```

No install the ElasticSearch Opendistro from AWS and make adjustments accordingly

``` bash
./install-es.sh --storage-size 50Gi --mem-size 1g --min-master-nodes 3 --replicas 6
```

No install the Kibana Opendistro from AWS and make adjustments accordingly and making sure that --es-repliucas is the same value as the --replicas in the install-es script

``` bash
./install-kibana.sh --kibana-replicas 2 --es-replicas 6
```

Next, copy certs into the proper files.  There is a proxy/web-proxy-certs directory.  Please update the files:

* **ca.crt** holds the root CA chain in PEM format
* **server.key** holds the Private key of the server in PEM format and password stripped
* **server.pem** holds the Public key of your server in PEM format.

Now install the proxy

``` bash
./install-proxy.sh
```

Now install the filebeats for logging the O2 cluster installation

``` bash
./install-filebeats.sh
```