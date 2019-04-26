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
sudo yum install -y ansible python-passlib git pyOpenSSL httpd-tools java-1.8.0-openjdk-headless
```

For disconnected environments, assume all dependency RPMs are in a common repo and have a repo file under /etc/yum.repo.d/ directory pointing to your common yum repository. 

```bash
sudo yum install -y ansible python-passlib git pyOpenSSL httpd-tools java-1.8.0-openjdk-headless
```

At the time of writing this document we are using ansible version **2.7.10**.  

If you have internet connectivity you can checkout openshift-ansible playbooks from the openshift project on github.

```bash
cd ~
git clone https://github.com/openshift/openshift-ansible.git
cd ~/openshift-ansible
git checkout release-3.11
```

If you do not have internet connectivity please either copy the RPM to a disconnected repo or grab a tarball that holds the openshift-ansible source and then extract to the home directory on the ansible machine. We will assume that the version is the same mentioned in this Documentation.

`tar xvfz openshift-ansible.tgz`

We have made no modifications to the installation playbooks and can be used as is.  Most of the playbooks have variables we can set in the inventory file to customize the installation process.

### Setup SSH Keys and Config

SSH is used by ansible to configure nodes in the cluster.  Each node must be reachable from the ansible configuration node.  Setup an ssh key for a common user so one can configure all nodes in the inventory. If you add a password to your ssh key you must use an ssh-agent on the ansible machine.  The ssh-agent will cache the password and encrypt it.  We will now copy this ssh id to all nodes in the cluster so the authorized_keys will be configured and setup for ssh on each node.  It is important to note that the **ssh user must have sudo rights** on each node for the ansible scripts will install items that require sudo privileges.  You can use the ssh-copy-id tool to handle setting up the authorized_keys, ... etc on the target machine.

```bash
mkdir ~/.ssh;chmod 700 ~/.ssh
ssh-keygen -f ~/.ssh/os-config-key-rsa -t rsa -b 4096
ssh-copy-id -i ~/.ssh/os-config-key-rsa user@host
```

If the **keys are password protected** then make sure the ssh-agent is running on the ansible machine and then add the key.

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
Host openshift-test-lb-node.private.ossim.io
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

If you have a gluster cluster that would need to be configured for openshift dynamic provisioning support then we will assume similar private dns names and you can run the following script

```bash
for x in {1..3}; do ssh openshift-test-glusterfs-$x.private.ossim.io "sudo yum install -y python-passlib java-1.8.0-openjdk-headless NetworkManager pyOpenSSL;sudo systemctl enable NetworkManager;sudo systemctl start NetworkManager"; done
```

Note, the gluster cluster here should have un-allocated disks and OpenShift installs heketi to add a restful interface for dynamically provisioning space from the gluster cluster.

### Dynamic Provisioning with Gluster

For the gluster ansible scripts to work, please make sure you have the latest CentOS7 and updates installed on your gluster nodes.  We will show the dynamic provisioning version of gluster.  This is not a statically installed gluster where the volumes are predefined and laid out.  The dynamic provisioning is facilitate through heketi and will carve out volumes from the gluster cluster on demand.  At the time of writing this document the version of CentOS that we know worked with the configuration setup is **CentOS Linux release 7.6.1810 (Core)**

The gluster interface allows one to dynamically provision volumes using heketi.  The current installation allows the gluster server to be installed as a daemonset into OpenShift.  This is indicated by the variables in the inventory file:

```config
openshift_storage_glusterfs_is_native=true
openshift_storage_glusterfs_heketi_is_native=true
openshift_storage_glusterfs_name="dynamic"
```

The storage class reference name used will be prefixed with glusterfs.  the keyword **openshift_storage_glusterfs_name** will indicate that a storage class reference **glusterfs-dynamic** can be used to reference the dynamic provisioner.

So the gluster will not have any worker pods scheduled to it we will redefined the node_groups and add another group called **node-config-compute-storage**.  At the time of writing this document we have not found a way to append to the current list of node groups so we have to specify all the groups we will need in the current list plus any additional groups.  

```config
openshift_node_groups=[{'name': 'node-config-master', 'labels': ['node-role.kubernetes.io/master=true']}, {'name': 'node-config-infra', 'labels': ['node-role.kubernetes.io/infra=true']}, {'name': 'node-config-compute', 'labels': ['node-role.kubernetes.io/compute=true']}, {'name': 'node-config-compute-storage', 'labels': ['node-role.kubernetes.io/compute-storage=true']}]
```

We can override the variable without editing the scripts but the original list can be found under the file **roles/openshift_facts/defaults/main.yml** relative form the the top level openshift-ansible directory.  Any node group can be copied out and added to the list


### Configure the Nodes in the Cluster

We now assume that you have a ~/.ssh/config file that describes how to reach each node in the cluster.  We will now place those nodes into the proper sections described in the annotated sample inventory file found in the directory **openshift/openshift-inventory-sample**.  Use this file to create an inventory file for your cluster in the ansible home ~/openshift-inventory.  The file has annotations explaining each section and must be tailored for your environment and resource limits.  If you only have a couple of machines to use for an OpenShift cluster then you can merge the definitions so they share machines.  For example,  you can have your master node, infra, and etcd all on one node and use the other node for compute only.  Please see the inventory example for further definitions.  

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

Once the cluster has been deployed we must setup the Security Context for the cluster to allow us to run as any user.  The OMAR services run as user 1000 and the ElasticSearch Opendistro cluster runs as user 1001.  The easiest thing to do is:

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

Also edit the restricted scc:

```bash
oc login -u system:admin
oc edit scc restricted
```

set the variables:

```yaml
allowPrivilegeEscalation: true
allowPrivilegedContainer: true

runAsUser:
  type: RunAsAny
```

then exit with the command sequence Escape key, then hit colin key ":" then "wq" key this will finally save the modifications.  We are now ready to install a sample ElasticCluster using our dynamic provisioning.

### Gluster Volume Types

Once the installation process is complete the default volume type added for the storageclass provisioner in OpenShift will replicate for redundancy unless you specify otherwise with the variable **openshift_storage_glusterfs_storageclass_volume_type** in your inventory file.  Your default storage class created should look something like this:

```yaml
apiVersion: v1
items:
- apiVersion: storage.k8s.io/v1
  kind: StorageClass
  metadata:
    name: glusterfs-dynamic
    namespace: ""
  parameters:
    resturl: http://heketi-dynamic.glusterfs.svc:8080
    restuser: admin
    secretName: heketi-dynamic-admin-secret
    secretNamespace: glusterfs
  provisioner: kubernetes.io/glusterfs
  reclaimPolicy: Delete
  volumeBindingMode: Immediate
kind: List
metadata:
  resourceVersion: ""
  selfLink: ""
```

We have provided a file called glusterfs-dynamic-norep.yml that is a no replication volumetype so it just distributes the blocks allocated.

```yaml
apiVersion: v1
items:
- apiVersion: storage.k8s.io/v1
  kind: StorageClass
  metadata:
    name: glusterfs-dynamic-norep
    namespace: ""
  parameters:
    resturl: http://heketi-dynamic.glusterfs.svc:8080
    restuser: admin
    secretName: heketi-dynamic-admin-secret
    secretNamespace: glusterfs
    volumetype: "none"
  provisioner: kubernetes.io/glusterfs
  reclaimPolicy: Delete
  volumeBindingMode: Immediate
kind: List
metadata:
  resourceVersion: ""
  selfLink: ""
```

Note, if you change the variable or add a variable called **openshift_storage_glusterfs_storageclass_volume_type** to the inventory file it will give you control over the volumetype allocated when provisioning new volumes.  The values can be:

* **none** specifies you want a storage class that does not enable replication on a volume
* **replicate:3** specifies you want the storage class to have a replication of 3

If you want to support replicated and non replicated volumetypes then you can add multiple storage classes but will have to be added after the installation is complete using this command:

```bash
oc create -f glusterfs-dynamic-norep.yml
```

To use this provisioner type you will need to use the name **glusterfs-dynamic-norep** instead of **glusterfs-dynamic** if you do not want to worry about replication.

Once you have defined your storage class you can use this to test the allocation of a claim.  In this example please modify the **storageClassName** to the name you created in your storage class list.  If you want to verify then:

```bash
oc get storageclass
```

Should print something of the form:

```text
NAME                PROVISIONER               AGE
glusterfs-dynamic   kubernetes.io/glusterfs   18h
```
Create a file called glusterfs-pvc.yml with contents:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
 name: gluster1
spec:
 accessModes:
  - ReadWriteMany
 resources:
   requests:
        storage: 1Gi
 storageClassName: glusterfs-dynamic
```

We will use the glusterfs project to test dynamic provision and assume you created a file called glusterfs-pvc.yml.

```bash
oc login -u system:admin
oc project glusterfs
oc create -f glusterfs-pvc.yml
oc get pvc
```

Should have output that shows your claim being bound glusterfs1.  Note it might take a second so if you run the oc get pvc right after the create you might not get the "Bound" state.

```text
gluster1   Bound     pvc-dbe9559b-6687-11e9-b140-0e3548ad372e   1Gi        RWX            glusterfs-dynamic   10s
```

To remove the volume just do

```bash
oc delete pvc gluster1
```

### Uninstalling

If you want to uninstall a cluster because of failure or you just want to do a fresh new install you can run the uninstall playbook:

```bash
cd ~/openshift-ansible
ansible-playbook -i ~/openshift-inventory playbooks/adhoc/uninstall.yml
```

If you want to completely wipe the glusterfs clean after you run the uninstall.yml you might have to do a `wipefs -a <device>` on all glusterfs nodes.  For example you can use this script as a template for a 6 node cluster:

You might have volume groups created and wipefs will error out.   If you want to remove everything then you must wipe the volumes created on the gluster devices on each node or you will not be able to re-install gluster.

```bash
for x in {1..6}; do echo $x;ssh openshift-test-glusterfs-$x.private.ossim.io "sudo vgremove -q -y \$(sudo vgdisplay|grep 'VG Name'|awk '{print \$3}');";done
```

Now wipe out each device.

```bash
for x in {1..6}; do ssh openshift-test-glusterfs-$x.private.ossim.io "sudo wipefs -a <device>";done
```
