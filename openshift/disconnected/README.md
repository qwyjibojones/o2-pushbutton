# Disconnected OpenShift 3.11 origin (Now OKD) Installation Dependencies


## Syncronizing Repos for Disconnected Installation

**Step 01.** [Syncrhonize the RPMs](./repo-sync)

*Notes:* For disconnected installations of OpenShift 3.11 we need to synchronize RPM repos for the containers that will be running in the OpenShift environment.

**Step 02.** [Download all Containers](./containers)

*Notes:* For disconnected installations of OpenShift 3.11 we need to download all images for the containers that will be running in the OpenShift environment. 

**Step 03.** Copy the server certificates 
```bash
  cp server-certs /data/disconnected/
```

*Notes:* The server-certs are self signed CERTS so we can proxy https.

**Step 04.** Copy the reverse proxy file
```bash
  cp reverse-proxy.conf /data/disconnected
```

## Load Dependencies

**Step 05.** By whatever witchcraft or wizardy that may be available get `/data/disconnected` and a copy of this repository to a disconnected location. It should look like this:
```bash
[centos]$ ls /data/disconnected | xargs -n 1
httpd.tgz
o2-pushbutton
registry
registry.tgz
reverse-proxy.conf
rpms
server-certs
```

**Step 06.** Ensure ansible is installed, first isntall the repo with the latest ansible and then install ansible, normally done with 

```bash
  sudo yum install -y git centos-release-ansible26
  sudo yum -y install ansible
 ```

**Step 07.** Ensure docker is installed, normally done with 

```bash
  sudo yum -y install docker
```

**Step 08.** Create a docker group 

```bash
  sudo groupadd docker
```

**Step 09.** Attach a user to the group 

```bash
  sudo usermod -aG docker centos
```

**Step 10.** Start the docker daemon

```bash
  sudo systemctl start docker
```

**Step 11.** Logout and log back in so the user modifications can take effect. 


### Serve out dependencies

**Step 12.** Load the registry container

```bash
  docker load -i /data/disconnected/registry.tgz
```

**Step 13.** Load the httpd container

```bash
  docker load -i /data/disconnected/httpd.tgz
```

*Notes:* We need to run the proxy server which serves as a https proxy to the docker registry and also serves up the YUM repository that we cached.

**Step 14.** Start the docker containers

```bash
  /data/disconnected/o2-pushbutton/openshift/disconnected/run-services.sh /data/disconnected
  ```

### Server Configuration

**Step 15.** Change the security context of the working directory 

```bash
  sudo chcon -Rt svirt_sandbox_file_t /data/disconnected
  ```

*Notes:* This will allow the directory and files to be accessed via a running container.

**Step 16.** Ensure port 5000 is open for the registry container

```bash
  firewall-cmd --zone-public --permanent --add-port=5000/tcp
  firewall-cmd --zone=public --add-service=http
  firewall-cmd --zone=public --add-service=https
  firewall-cmd --reload
```

**Step 17.** Enable selinus for web access on the installer 

```bash
  sudo setsebool -P httpd_can_network_connect on
  ```

**Step 18.** Add IP forwarding to all nodes

```bash
  sudo bash -c 'echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.d/99-sysctl.conf'
  sudo sysctl --load /etc/sysctl.d/99-sysctl.conf
```

**Step 19.** Test the docker registry

```bash
  curl -k https://localhost/v2/_catalog
  {"repositories":["cockpit/kubernetes","coreos/cluster-monitoring-operator","coreos/configmap-reload","coreos/etcd","coreos/kube-rbac-proxy","coreos/kube-state-metrics","coreos/prometheus-config-reloader","coreos/prometheus-operator","grafana/grafana","openshift/oauth-proxy","openshift/origin-console","openshift/origin-control-plane","openshift/origin-deployer","openshift/origin-docker-registry","openshift/origin-haproxy-router","openshift/origin-metrics-cassandra","openshift/origin-metrics-hawkular-metrics","openshift/origin-metrics-heapster","openshift/origin-metrics-schema-installer","openshift/origin-metrics-server","openshift/origin-node","openshift/origin-pod","openshift/origin-service-catalog","openshift/origin-template-service-broker","openshift/origin-web-console","openshift/prometheus","openshift/prometheus-alertmanager","openshift/prometheus-node-exporter"]}
  
  curl -k https://localhost/v2/openshift/origin-metrics-hawkular-metrics/tags/list
  {"name":"openshift/origin-metrics-hawkular-metrics","tags":["v3.11","v3.11.0"]}
```
