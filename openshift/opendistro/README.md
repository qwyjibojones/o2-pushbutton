# Install Guide for Opendistro ElasticSearch Into OpenShift Environment

Prerequisite of ElasticSearch requires you to bump up the vm.max_map_count=262144. There is a file supplied in this repository found under the directory node-config/99-es-stack.conf.  This file needs to be copied to all nodes in the cluster.  Example, lets assume that you have a DNS prefix of openshift-test-node-1.mysubdomain.io and you have 6 nodes in your cluster then:

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

We have supplied security-configmap/securityconfig directory that contains the security config for the latest release.  We will need to do several things before we start elasticsearch so we can have an initial admin password.

We will first need to generate a new password hash for our admin user.  You can also do the same for all the other internal users that have been supplied in the [internal_users.yml](security-configmap/securityconfig/internal_users.yml)

```bash
docker run -it --rm amazon/opendistro-for-elasticsearch:latest bash /usr/share/elasticsearch/plugins/opendistro_security/tools/hash.sh`
```

Copy that hash and put it into the internal_users.yml file and replace the current admin hash.  You can do this for all the other internal users users, just repeat for each user or you can have the same hash for all the internal users.  Now specify the password in the logging/filebeat.yml and replace the password.  Make sure you use the password and not the hash here:

```yaml
        env:
        - name: ELASTICSEARCH_HOST
          value: https://kibana.es-stack.endpoints.cluster.local:9200
        - name: ELASTICSEARCH_PORT
          value: "9200"
        - name: ELASTICSEARCH_USERNAME
          value: admin
        - name: ELASTICSEARCH_PASSWORD
          value: admin
```

we will now create a config map that contains the new password

`oc create configmap securityconfig --from-file=security-configmap/securityconfig`

Now make sure you are in this directory where this README is located and execute the commands that follow to install the cluster

Next build the elasticsearch image and kibana image

``` bash
./build-push.sh
```

No install the ElasticSearch Opendistro from AWS and make adjustments accordingly

```text
Usage: ./install-es.sh [options]
 options:
     --help Display this help
     --replicas Define the number of nodes in the cluster
     --min-master-nodes Define the number of nodes in the cluster
     --mem-size Mem size formatted in JAVA: Example 512m for 512 megabytes
                or 2g for 2 gigs
     --es-image Is the source image stream to pull from
                example: docker-registry.default.svc:5000/es-stack/es-app:latest
     --storage-size Formated in Openshift form of Storage sizes
                10Gi is ten gigs or 1Ti is one terrabyte
     --storage-class-name Specify the class name to use for the dynamic provisioning
                          For aws you can specify gp2.   For glusterfs you can specify
                          glusterfs-dynamic and if you installed the norep for 'No Replicatioun'
                          you can use the value glusterfs-dynamic-norep
     --project-namespace Give the namespace you wish to push the images to


Example:
     ./install-es.sh --replicas 3 --storage-class-name glusterfs-dynamic-norep --storage-size 10Gi --mem-size 1g
     ./install-es.sh --storage-size 200Gi --mem-size 2g --min-master-nodes 4 --replicas 6
     ./install-es.sh --es-image <registry and image> --kibana-image <registry and image> --project-namespace <Some namespace other than es-stack> --storage-size 200Gi --mem-size 2g --min-master-nodes 4 --replicas 6
     ./install-es.sh --storage-size 200Gi --mem-size 2g --min-master-nodes 4 --replicas 6
```

If you change the namespace you must explicitly specify the path to the es-image and the kibana-image.

```bash
./install-es.sh --storage-size 200Gi --mem-size 2g --min-master-nodes 4 --replicas 6
```

Now install the Kibana Opendistro from AWS and make adjustments accordingly and making sure that --es-replicas is the same value as the --replicas in the install-es script

```text
Usage: ./install-kibana.sh [options]
 options:
     --help Display this help
     --es-replicas This is the number of nodes defined in the
                   elastic search cluster previously executed
                   by the install-es.sh
     --kibana-replicas This is the number of kibana replicas to set on startup
     --es-image Is the source elasticsearch image stream to pull from
                defaults to: docker-registry.default.svc:5000/es-stack/es-app:latest
     --kibana-image Is the source kibana image stream to pull from
                defaults to: docker-registry.default.svc:5000/es-stack/kibana-app:latest
     --project-namespace Give the namespace you wish to push the images to

 examples:
      ./install-kibana.sh --kibana-replicas 2 --es-replicas 6
    
```

If you change the namespace you must explicitly specify the path to the es-image and the kibana-image.


Next, copy certs into the proper files.  There is a proxy/web-proxy-certs directory.  Please update the files:

* **ca.crt** holds the root CA chain in PEM format
* **server.key** holds the Private key of the server in PEM format and password stripped
* **server.pem** holds the Public key of your server in PEM format.

Now install the proxy

``` bash
./install-proxy.sh
```

Now install the filebeats for logging the O2 cluster installation.

``` bash
./install-filebeats.sh
```