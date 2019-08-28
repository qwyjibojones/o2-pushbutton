# Disconnected OpenShift 3.11 origin (Now OKD) Installation Dependencies


## Syncronizing Repos for Disconnected Installation

**Step 01.** [Syncrhonize the RPMs](../../../repo-sync/README.md)

*Notes:* For disconnected installations of OpenShift 3.11 we need to synchronize RPM repos for the containers that will be running in the OpenShift environment.

**Step 02.** [Download all Containers](./containers/README.md)

*Notes:* For disconnected installations of OpenShift 3.11 we need to download all images for the containers that will be running in the OpenShift environment.  for convenience we supplied a bundle-all for the containers and copying all required shell scripts to run the registry and proxy

```bash
./bundle-all.sh /data/disconnected
```

## Load Dependencies

**Step 03.** By whatever witchcraft or wizardy that may be available get `/data/disconnected` and a copy of this repository to a disconnected location. It should look like this:
```bash
[centos]$ ls /data/disconnected | xargs -n 1
docker-images
registry
remove-services.sh
reverse-proxy.conf
rpms
run-services.sh
server-certs
```

**Step 04.** Ensure ansible is installed, first isntall the repo with the latest ansible and then install ansible, normally done with 

```bash
  sudo yum install -y git centos-release-ansible26
  sudo yum -y install ansible
 ```

**Step 05.** Ensure docker is installed, normally done with 

```bash
  sudo yum -y install docker
```

**Step 06.** Create a docker group 

```bash
  sudo groupadd docker
```

**Step 07.** Attach a user to the group 

```bash
  sudo usermod -aG docker centos
```

**Step 08.** Start the docker daemon

```bash
  sudo systemctl start docker
```

**Step 09.** Logout and log back in so the user modifications can take effect. 


### Serve out dependencies

**Step 10.** Load the registry container

```bash
  docker load -i /data/disconnected/docker-images/registry.tgz
```

**Step 11.** Load the httpd container

```bash
  docker load -i /data/disconnected/docker-images/httpd.tgz
```

*Notes:* We need to run the proxy server which serves as a https proxy to the docker registry and also serves up the YUM repository that we cached.

**Step 12.** Start the docker containers

```bash
  /data/disconnected/run-services.sh /data/disconnected
```

### Server Configuration

**Step 13.** Change the security context of the working directory 

```bash
  sudo chcon -Rt svirt_sandbox_file_t /data/disconnected
```

*Notes:* This will allow the directory and files to be accessed via a running container.

**Step 14.** Ensure port 5000 is open for the registry container

```bash
  firewall-cmd --zone-public --permanent --add-port=5000/tcp
  firewall-cmd --zone=public --add-service=http
  firewall-cmd --zone=public --add-service=https
  firewall-cmd --reload
```

**Step 15.** Enable selinus for web access on the installer 

```bash
  sudo setsebool -P httpd_can_network_connect on
  ```

**Step 16.** Add IP forwarding to all nodes

```bash
  sudo bash -c 'echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.d/99-sysctl.conf'
  sudo sysctl --load /etc/sysctl.d/99-sysctl.conf
```

**Step 17.** Test the docker registry

```bash
  curl -k https://localhost/v2/_catalog
  {"repositories":["cockpit/kubernetes","coreos/cluster-monitoring-operator","coreos/configmap-reload","coreos/etcd","coreos/kube-rbac-proxy","coreos/kube-state-metrics","coreos/prometheus-config-reloader","coreos/prometheus-operator","grafana/grafana","openshift/oauth-proxy","openshift/origin-console","openshift/origin-control-plane","openshift/origin-deployer","openshift/origin-docker-registry","openshift/origin-haproxy-router","openshift/origin-metrics-cassandra","openshift/origin-metrics-hawkular-metrics","openshift/origin-metrics-heapster","openshift/origin-metrics-schema-installer","openshift/origin-metrics-server","openshift/origin-node","openshift/origin-pod","openshift/origin-service-catalog","openshift/origin-template-service-broker","openshift/origin-web-console","openshift/prometheus","openshift/prometheus-alertmanager","openshift/prometheus-node-exporter"]}
  
  curl -k https://localhost/v2/openshift/origin-metrics-hawkular-metrics/tags/list
  {"name":"openshift/origin-metrics-hawkular-metrics","tags":["v3.11","v3.11.0"]}
```
