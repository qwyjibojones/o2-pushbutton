# OpenShift-3.11 Bare Metal Installation and Configuration

If we do not have the luxury of being able to host or install OpenShift within a cloud environment and be able to use one of their cloud installation scripts we will need to configure and deploy OpenShift "manually".  When we say "manual" we have to configure each bare-metal machine with some initial settings before the openshift-ansible scripts can be ran to setup the cluster as an OpenShift environment.

For this example installation process we will use one node for master and infra and compute and will have DNS names:

* openshift-test-master-node-1.ossim.io
* openshift-test-infra-node-1.ossim.io
* openshift-test-compute-node-1.ossim.io

Please rename accordingly for your installation.  For a production install you probably would want at least 2 or 3 masters and 2 infra nodes that route service traffic within the cluster.  The compute or "worker nodes" typically handle all the main processing pods.  The number of compute nodes will allow one to horizontally scale compute power by increasing the pod count and if the pod count exceeds the resource you can add another compute node to the cluster and keep horizontally scaling.

Before we begin.  Please have a wildcard NPE Certificate that we will use for the master and router certificates.  We will also use the same CERT for the Hawkular metrics installation.

## Ansible

We will need a machine running ansible that will be used to configure and setup the OpenShift cluster.  The ansible machine does not need to be very powerful, for it is only used for cluster configuration.  The machine uses ansible to configure your OpenShift cluster using the openshift-ansible playbooks.  If you are limited on resources, you can use the node that will be dedicated to the OpenShift master as your ansible machine.  It is best to have a separate ansible machine dedicated to the configuration of the cluster, so if you need to destroy the cluster and re-install, you still have your configuration machine in tact.

### Install Ansible

For disconnected networks we will assume that the /etc/yum.repo.d/ directory has files that are pointing to your local yum repo that holds all the base RPMS for a CentOS distribution including any updates and extras.

For connected environments:

```bash
sudo yum install -y git centos-release-ansible26
sudo yum install -y ansible
```

For disconnected environments, assume all dependency RPMs are in a common repo and have a repo file under /etc/yum.repo.d/ directory pointing to your common yum repository.

```bash
sudu yum install -y ansible
```


If you have internet connectivitiy you can checkout ansible from the openshift project on github.

```bash
cd ~
git clone https://github.com/openshift/openshift-ansible.git
cd ~/openshift-ansible
git checkout remotes/origin/release-3.11
```

If you do not have internet connectivity please use either copy the RPM to a disconnected repo or grab a  tarball that holds the openshift-ansible source and then extract to the home directory on the ansible machine. We will assume that the version is the same mentioned in this Documentation.

`tar xvfz openshift-ansible.tgz`

### Setup SSH Keys and Config

SSH is used by ansible to configure nodes in the cluster.  Each node must be reachable from the ansible configuration node.  Setup an ssh key for a common user so one can configure all nodes in the inventory.  If you add a password to your ssh key you must use an ssh-agent on the ansible machine.  The ssh-agent will cache the password and encrypt it.  We will now copy this ssh id to all nodes in the cluster so the authorized_keys will be configured and setup for ssh on each node.  It is important to note that the ssh user must have sudo rights on each node for the ansible scripts will install items that require sudo privileges.  You can use the ssh-copy-id tool to handle setting up the authorized_keys, ... etc on the target machine.

```bash
mkdir ~/.ssh;chmod 700 ~/.ssh
ssh-keygen -f ~/.ssh/os-config-key-rsa -t rsa -b 4096
ssh-copy-id -i ~/.ssh/os-config-key-rsa user@host
```

If the **keys are password protected** then make sure the ssh-agent is running and then add the key.

```bash
ssh-agent
ssh-add ~/.ssh/os-config-key-rsa
```

create ~/.ssh/config on your ansible machine with contents listing all nodes in your cluster

```config
Host openshift-test-master-node-1.private.ossim.io
  User centos
  IdentityFile ~/.ssh/os-config-key-rsa
Host openshift-test-infra-node-1.private.ossim.io
  User centos
  IdentityFile ~/.ssh/os-config-key-rsa
Host openshift-test-compute-node-1.private.ossim.io
  User centos
  IdentityFile ~/.ssh/os-config-key-rsa
```

change the permissions to be 600: `chmod 600 ~/.ssh/config`

Setup NetworkManager and python ssl on all nodes.  If you have your nodes in the config named with numbers 1-n then it's a simple bash script and can be done for each dns prefix.  In this example all of our nodes are prefixed with openshift-test-node-.  When metrics are enabled we must add to the install java headless and python-passlib.  Please modify these bash commands to match the number of nodes and dns values:

```bash
for x in {1..3}; do ssh openshift-test-master-node-$x.private.ossim.io "sudo yum install -y python-passlib java-1.8.0-openjdk-headless NetworkManager pyOpenSSL;sudo systemctl enable NetworkManager;sudo systemctl start NetworkManager"; done
for x in {1..1}; do ssh openshift-test-infra-node-$x.private.ossim.io "sudo yum install -y python-passlib java-1.8.0-openjdk-headless NetworkManager pyOpenSSL;sudo systemctl enable NetworkManager;sudo systemctl start NetworkManager"; done
for x in {1..8}; do ssh openshift-test-compute-node-$x.private.ossim.io "sudo yum install -y python-passlib java-1.8.0-openjdk-headless NetworkManager pyOpenSSL;sudo systemctl enable NetworkManager;sudo systemctl start NetworkManager"; done
```

### Dyanmic Provisioning with Gluster

For the gluster ansible scripts to work, please make sure you have the latest CentOS7 and updates installed on your gluster nodes.  We will show the dynamic provbisioning version of gluster.  This is not a statically installed gluster where the volumes are predefined and laid out.  The dynamic provisioning is facilitate through heketi and will carve out volumes from the gluster cluster on demand.  At the time of writing this document the version of CentOS that we know worked with the configuration setup is **CentOS Linux release 7.6.1810 (Core)**

The gluster interface allows one to dynamically provision volumes using heketi.  The current installation allows the gluster server to be installed as a daemonset into OpenShift.  This is indicated by the variables in the inventory file:

```config
openshift_storage_glusterfs_is_native=true
openshift_storage_glusterfs_heketi_is_native=true
openshift_storage_glusterfs_name="dynamic"
```

The storage class reference name used will be prefixed with glusterfs.  the keyword **openshift_storage_glusterfs_name** will indicate that a storage class reference **glusterfs-dynamic** can be used to reference the dynamic provisioner.

### Configure the Nodes in the Cluster

We now assume that you have a ~/.ssh/config file that describes how to reach each node in the cluster.  We will now place those nodes into the proper sections described in the annotated sample inventory file found in the directory **openshift/openshift-inventory-sample**.  Use this file to create an inventory file for your cluster in the ansible home ~/openshift-inventory.  The file has annotations explaining each section and must be taylored for your environment and resource limits.   If you only have a couple of machines to use for an OpenShift cluster then you can merge the definionts so they share machines.  For example,  you can have your master node, infra, and etcd all on one node and use the other node for compute only.  Please see the inventory example for further definitions.  

Copy  and edit the inventory file

```bash
cp openshift/openshift-inventory-sample ~/openshift-inventory
vi ~/openshift-inventory
```

Put your node name into each section the node corresponds to.  SSH to each node in the config.  This will verify that the ansible machine can reach all nodes and are part of the known_hosts.

If all the nodes are reachable and ready to be configured then run:

```bash
cd ~/openshift-ansible
ansible-playbook -i ~/openshift-inventory playbooks/prerequisites.yml
ansible-playbook -i ~/openshift-inventory playbooks/deploy_cluster.yml
```

Once the cluster has been deployed we must setup the Security Context for the cluster to allow us to run as any user.  The OMAR services run as user 1000 and the ElasticSearch Opendistro cluster runs as user 1001.  The easiest thing is the do:

```bash
oc login -u system:admin
oc edit scc privileged
```

set the variables:

```yaml
allowPrivilegeEscalation: true
allowPrivilegedContainer: true

runAsUser:
  type: RunAsAny
```

then exit with the command sequence Escape key, then hit colin key ":" then "wq" key this will finally save the modifications.  We are now ready to install a sample ElasticCluster using our dynamic proviisioning.

### Uninstalling

If you want to uninstall a cluster because of failure or you just want to do a fresh new install you can run the uninstall playbook:

```bash
cd ~/openshift-ansible
ansible-playbook -i ~/openshift-inventory playbooks/adhoc/uninstall.yml
```

If you want to completely wipe the glustersfs clean after you run the uninstall.yml you might have to do a `wipefs -a` on all glusterfs nodes.  For example you can use this script as a template for a 6 node cluster:

```bash
for x in {1..6}; do ssh openshift-test-glusterfs-$x.private.ossim.io "sudo wipefs -a <device>"; 
```