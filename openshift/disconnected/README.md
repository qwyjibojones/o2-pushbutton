# Disconnected OpenShift 3.11 origin (Now OKD) Installation Dependencies


## Syncronizing Repos for Disconnected Installation

**Step 01.** [Syncrhonize the RPMs](./repo-sync)

*Notes:* For disconnected installations of OpenShift 3.11 we need to synchronize RPM repos for the containers that will be running in the OpenShift environment.

**Step 02.** [Download all Containers](./containers)

*Notes:* For disconnected installations of OpenShift 3.11 we need to download all images for the containers that will be running in the OpenShift environment. 

**Step 03.**
```bash
  cp server-certs /data/disconnected/
  cp reverse-proxy.conf /data/disconnected
```

*Notes:* The server-certs are self signed CERTS so we can proxy https.


## Load Dependencies

**Step 04.** By whatever witchcraft or wizardy that may be available get `/data/disconnected` and a copy of this repository to a disconnected location. It should look like this:
```bash
[centos]$ ls -l /data/disconnected
httpd.tgz
o2-pushbutton
registry
registry.tgz
reverse-proxy.conf
rpms
server-certs
```

**Step 05.** Ensure ansible is installed, normally done with `sudo yum -y install ansible`

**Step 06.** Ensure docker is installed, normally done with `sudo yum -y install docker`

**Step 07.** Create a docker group: `sudo groupadd docker`

**Step 08.** Attach a user to the group: `sudo usermod -aG docker centos`

**Step 09.** Start the docker daemon: `sudo systemctl start docker`

**Step 10.** Logout and log back in so the user modifications can take effect. 


### Serve out dependencies

**Step 11.**
```bash
  docker load -i /data/disconnected/registry.tgz
  docker load -i /data/disconnected/httpd.tgz
```

*Notes:* We need to run the proxy server which serves as a https proxy to the docker registry and also serves up the YUM repository that we cached.

**Step 12.** Start the docker containers: `/data/disconnected/o2-pushbutton/openshift/disconnected/run-services.sh /data/disconnected`


### Server Configuration

**Step 13.** Change the security context of the working directory: `sudo chcon -Rt svirt_sandbox_file_t /data/disconnected`

*Notes:* This will allow the directory and files to be accessed via a running container.

**Step 14.** Ensure port 5000 is open for the registry container:
```bash
  firewall-cmd --zone-public --permanent --add-port=5000/tcp
  firewall-cmd --zone=public --add-service=http
  firewall-cmd --zone=public --add-service=https
  firewall-cmd --reload
```

**Step 15.** Enable selinus for web access on the installer: `sudo setsebool -P httpd_can_network_connect on`

**Step 16.** Add IP forward to all nodes: 
```bash
  sudo bash -c 'echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.d/99-sysctl.conf'
  sudo sysctl --load /etc/sysctl.d/99-sysctl.conf
```

**Step 17.** Test the docker registry: 
```bash
  curl -k https://localhost/v2/_catalog
  curl -k https://localhost/v2/<image-path-and-name>/tags/list
```
