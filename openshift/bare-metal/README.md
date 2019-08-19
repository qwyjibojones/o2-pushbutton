# OpenShift-3.11 Bare Metal Installation and Configuration

## Requirements

For completeness we will repeat from the Origin Documentation for 3.11 the Hardware Requirements but tailored to our CentOS7 environment.

* **Master Hardware**
  - Physical or virtual system or an instance running on a public or private IaaS.
  - Base OS: CentOS 7.6. We were testing on at least **CentOS Linux release 7.6.1810 (Core)**
  - Minimum 4 vCPU (additional are strongly recommended).
  - Minimum 16 GB RAM (additional memory is strongly recommended, especially if etcd is co-located on masters).
  - Minimum 40 GB hard disk space for the file system containing /var/.
  - Minimum 1 GB hard disk space for the file system containing /usr/local/bin/.
  - Minimum 1 GB hard disk space for the file system containing the system’s temporary directory.
  - Masters with a co-located etcd require a minimum of 4 cores. Two-core systems do not work.
* **Node Hardware**
  - Physical or virtual system, or an instance running on a public or private IaaS.
  - Base OS: CentOS 7.6.  We were testing on at least **CentOS Linux release 7.6.1810 (Core)**
  - NetworkManager 1.0 or later.
  - 1 vCPU.
  - Minimum 8 GB RAM.
  - Minimum 15 GB hard disk space for the file system containing /var/.
  - Minimum 1 GB hard disk space for the file system containing /usr/local/bin/.
  - Minimum 1 GB hard disk space for the file system containing the system’s temporary directory.
  - An additional minimum 15 GB unallocated space per system running containers for Docker’s storage back end.
* **External Etcd**
  - Minimum 20 GB hard disk space for etcd data.
  - See the Hardware Recommendations section of the CoreOS etcd documentation for information how to properly size your etcd nodes.
  - Currently, OKD stores image, build, and deployment metadata in etcd. You must periodically prune old resources. If you are planning to leverage a large number of these resources, place etcd on machines with large amounts of memory and fast SSD drives.
* **System Admin Knowledge** One will need to have some level of training in System Administration and bash scripting.
* **Repos**
  - openshift-ansible This will be a checkout or tar ball of release-3.11.  Repo can be found here [https://github.com/openshift/openshift-ansible](https://github.com/openshift/openshift-ansible)
  - o2-pushbutton repo can be found here [https://github.com/ossimlabs/o2-pushbutton](https://github.com/ossimlabs/o2-pushbutton)
  
* **NPE Certificate** We prefer that you have a valid wildcard NPE certificate that we can use.  If this is in the format of a .p12 we will need to convert into a pem and key without a password and have the CA available.  If you do not have the ability to use a wildcard NPE CERT that is fine. You will at the minimum need an NPE CERT for the okd hawkular metrics and OKD master web console endpoints.  Additional NPE CERTS will be needed for any web applications installed on the cluster that needs to serve via https.

If we do not have the luxury of being able to host or install OpenShift within a cloud environment and be able to use one of their cloud installation scripts we will need to configure and deploy OpenShift "manually".  When we say "manually" we have to configure each bare-metal machine with some initial settings before the openshift-ansible scripts can be ran to setup the cluster as an OpenShift environment.

For this example installation process we will use one node for master, infra and compute and will have DNS names:

* `openshift-test-master-node-1.foo.io`
* `openshift-test-infra-node-1.foo.io`
* `openshift-test-compute-node-1.foo.io`

Please rename accordingly for your installation.  For a production install you probably would want at least 2 or 3 masters and 2 infra nodes that route service traffic within the cluster. If you are limited on resources you can double up the infra and put the infra support on the master nodes.  The compute or "worker nodes" typically handle all the main processing pods.  The number of compute nodes will allow one to horizontally scale compute power by increasing the pod count and if the pod resources exceeds the resources of your cluster then you can add another compute node to the cluster and keep horizontally scaling.

Before we begin, please have your NPE Certificate(s) for each endpoint hosted via https which at a minimum will be hawkular, and the web console.

## Ansible

We will need a machine running ansible that will be used to configure and setup the OpenShift cluster.  The ansible machine does not need to be very powerful, for it is only used for cluster configuration.  We will also use the ansible host as a disconnected machine that will serve up the OpenShift origin containers and the RPMS used during the installation process.  The machine uses ansible to configure your OpenShift cluster using the openshift-ansible playbooks.  If you are limited on resources, you can use the node that will be dedicated to the OpenShift master as your ansible machine.  It is best to have a separate ansible machine dedicated to the configuration of the cluster, so if you need to destroy the cluster and re-install, you still have your configuration machine in tact.

### Install Ansible

We have supplied a mechanism that uses docker to serve up openshift related RPM and container dependencies.  For disconnected networks we will assume that the /etc/yum.repo.d/ directory has files that are pointing to a yum repo that holds all the base RPMS for a CentOS distribution including any updates and extras.  If you do not have these then these could be added to our RPM tree as described in this [README](../disconnected/README.md)

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
# for disconnected create a tarball
cd ~
tar cvfz openshift-ansible.tgz openshift-ansible
```

If you are disconnected then the openshift-ansible repo will need to be tarballed up and then extracted to the home/working directory of an install user on the ansible machine. We will assume that the version is the same mentioned in this Documentation, release-3.11.

`tar xvfz openshift-ansible.tgz`

We have made no modifications to the installation playbooks and can be used as is.  Most of the playbooks have variables we can set in the inventory file to customize the installation process.

### Setup SSH Keys and Config

SSH is used by ansible to configure nodes in the cluster.  Each node must be reachable from the ansible configuration node.  Setup an ssh key for a common user so one can configure all nodes in the inventory. The preferred way is to create an ssh key without a password.  If you add a password to your ssh key you must use an ssh-agent on the ansible machine.  The ssh-agent will cache the password and encrypt it.  We will now copy this ssh id to all nodes in the cluster so the authorized_keys will be configured and setup for ssh on each node.  It is important to note that the **ssh user must have sudo rights** on each node, for the ansible scripts will install items that require sudo privileges.  You can use the ssh-copy-id tool to handle setting up the authorized_keys, ... etc on the target machine.

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

`create ~/.ssh/config` on your ansible machine with contents listing all nodes in your cluster

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

**Note**: when you start the installation and you see messages of the form  `RETRYING: Wait for the ServiceMonitor CRD to be created` you will need to make sure you enable ip forwarding on all nodes see [Ip Forwarding Must Be Enable](#ip-forwarding-must-be-enable) section on how to set the value.

If you have a gluster cluster that would need to be configured for openshift dynamic provisioning support then we will assume similar private dns names and you can run the following script

```bash
for x in {1..3}; do ssh openshift-test-glusterfs-$x.private.ossim.io "sudo yum install -y python-passlib java-1.8.0-openjdk-headless NetworkManager pyOpenSSL;sudo systemctl enable NetworkManager;sudo systemctl start NetworkManager"; done
```

Note, the gluster cluster here should have un-allocated disks and OpenShift installs heketi to add a restful interface for dynamically provisioning space from the gluster cluster.

### Dynamic Provisioning with Gluster

For the gluster ansible scripts to work, please make sure you have the latest CentOS7 and updates installed on your gluster nodes.  We will show the dynamic provisioning via heketi.  The dynamic provisioning is facilitated through heketi and will carve out volumes from the gluster cluster on demand.  At the time of writing this document the version of CentOS that we know worked with the configuration setup is **CentOS Linux release 7.6.1810 (Core)**.  Note, when the openshift installation gets to heketi and it loads the topology it seems to take a while, so please be patient.

The gluster interface allows one to dynamically provision volumes using heketi.  The current installation allows the gluster server to be installed as a daemonset into OpenShift.  This is indicated by the variables in the inventory file:

```config
openshift_storage_glusterfs_is_native=true
openshift_storage_glusterfs_heketi_is_native=true
openshift_storage_glusterfs_name="dynamic"
```

A gluster server is installed on every node listed in the **[glusterfs]** section.

The storage class reference name used will be prefixed with glusterfs.  the keyword **openshift_storage_glusterfs_name** will indicate that a storage class reference **glusterfs-dynamic** can be used to reference the dynamic provisioner.

So the gluster will not have any worker pods scheduled to it, we will redefined the node_groups and add another group called **node-config-compute-storage**.  At the time of writing this document we have not found a way to append to the current list of node groups so we have to specify all the groups we will need in the current list plus any additional groups.  We can make this much more readable by using an external variables file and cut and paste the values from the main.yml and put into our YAML inventory vars file.   In this example we show the format in the inventory file.  

```config
openshift_node_groups=[{'name': 'node-config-master', 'labels': ['node-role.kubernetes.io/master=true']}, {'name': 'node-config-infra', 'labels': ['node-role.kubernetes.io/infra=true']}, {'name': 'node-config-compute', 'labels': ['node-role.kubernetes.io/compute=true']}, {'name': 'node-config-compute-storage', 'labels': ['node-role.kubernetes.io/compute-storage=true']}]
```

We can override the variable without editing the scripts but the original list can be found under the file **roles/openshift_facts/defaults/main.yml** relative from the the top level openshift-ansible directory.  Any node group can be copied out and added to the list.

### Configure the Nodes in the Cluster

We now assume that you have a ~/.ssh/config file that describes how to reach each node in the cluster.  We will now place those nodes into the proper sections described in the annotated sample inventory file found in the directory **[openshift/openshift-inventory-sample](openshift/openshift-inventory-sample)**.  Use this file to create an inventory file for your cluster in the ansible home ~/openshift-inventory.  The file has annotations explaining each section and must be tailored for your environment and resource limits.  If you only have a couple of machines to use for an OpenShift cluster then you can merge the definitions so they share machines.  For example,  you can have your master node, infra, and etcd all on one node and use the other node for compute only.  Please see the inventory example for further definitions.  

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

defaultAddCapabilities:
- SYS_ADMIN

runAsUser:
  type: RunAsAny
```

**Note:** The defaultAddCapabilities might be set to NULL initially.  This is needed for some of the pods that wish to have s3 mounting via goofys.

then exit with the command sequence Escape key, then hit colin key ":" then "wq" key this will save the modifications.  We are now ready to install a sample ElasticCluster using our dynamic provisioning.

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

We have provided a file called glusterfs-dynamic-norep.yml that is a no replication volume type so it just distributes the blocks allocated indicated by the **volumetype: none**.

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

Note, if you change the variable or add a variable called **openshift_storage_glusterfs_storageclass_volume_type** to the inventory file it will give you control over the default **volumetype** allocated when provisioning new volumes.  The values can be:

* **none** specifies you want a storage class that does not enable replication on a volume
* **replicate:3** specifies you want the storage class to have a replication of 3
* **disperse:4:2** specifies a 4 data bricks and 2 replicas. The "disperse 4" means that each disperse-set is made of 4 bricks. "redundancy 2" means that two of those bricks will be redundant (i.e. it will work fine with 2 bricks down). Disperse doesn't allow redundancies greater or equal to "number of bricks" / 2. With redundancy 2, the minimum number of bricks/servers should be 5. Which is in reference to this response [https://lists.gluster.org/pipermail/gluster-users/2016-June/027022.html](https://lists.gluster.org/pipermail/gluster-users/2016-June/027022.html). Regarding the disperse, the minimum number of servers you would need is 3. Disperse requires at least 3 bricks to create a configuration with redundancy 1 (this is equivalent to a replica 2 in terms of redundancy), but if you put 2 of those bricks in a single server and that server dies, you will lose 2 bricks from a volume that only tolerates 1 brick failure.  For more information on disperse please see the [Gluster Documentation](https://docs.gluster.org/en/latest/Administrator%20Guide/Managing%20Volumes/).  This volume type is typically a little slower than the **replicate** type but in general is less wasteful on disk space.

If you want to support replicated and non replicated volume types then you can add multiple storage classes but will have to be added after the installation is complete using this command:

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

To test our provisioner, create a file called glusterfs-pvc.yml with contents:

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

Should have output that shows your claim being bound gluster1.  Note it might take a second so if you run the oc get pvc right after the create you might not get the "Bound" state.

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

If you want to completely wipe the glusterfs clean after you run the uninstall.yml you might have to do a `wipefs -a <device>` on all glusterfs nodes.  For example you can use this script as a template for a 6 node gluster cluster:

You might have volume groups created and wipefs will error out.   If you want to remove everything then you must wipe the volumes created on the gluster devices on each node or you will not be able to re-install gluster.

```bash
for x in {1..6}; do echo $x;ssh openshift-test-glusterfs-$x.private.ossim.io "sudo vgremove -q -y \$(sudo vgdisplay|grep 'VG Name'|awk '{print \$3}');";done
```

Now wipe out each device.  This script will need to be ran for each block device on the gluster nodes.

```bash
for x in {1..6}; do ssh openshift-test-glusterfs-$x.private.ossim.io "sudo wipefs -a <device>";done
```

## Tips

### Evacuate and drain Nodes

If for some reason a node is needing to be removed or something has happened to the node and you want to safely remove it or you just need to update and then reboot the node then you will need to make the node not schedulable and drain any pods that are currently running on the node:

```bash
oc adm manage-node <node> --schedulable=false
oc adm drain <node> --ignore-daemonsets
```

The node should no longer be scheduling and have any pods running on it.  We can now safely update or remove the node.  If we want to remove the node we can do:

```bash
oc delete node <node>
```

### Ip Forwarding Must Be Enable

For the OpenShift pod to write out the network settings the ip forwarding must be enabled on all the nodes.

* check the file /etc/sysctl.d/99-sysctl.conf file for the variable net.ipv4.ip_forward and make sure it is enabled with the value of 1.
* sudo systctl --load /etc/sysctl.d/99-sysctl.con

### IPSEC

* https://roll.urown.net/ca/ca_root_setup.html
* https://gist.github.com/fntlnz/cf14feb5a46b2eda428e000157447309
* https://docs.openshift.com/container-platform/3.11/admin_guide/ipsec.html

We can use the Openshift cluster certificates generated during installation but for now we will do our own CA and self signed certificates.

First let's create a root directory for our CA and all derived CERTS.  We can for now use the installer node to also be our Root CA for signing new certs for nodes in the cluster.

```bash
mkdir -p example.net.ca/root-ca/{certreqs,certs,crl,newcerts,private}
cd example.net.ca/root-ca
chmod 700 private
touch root-ca.index
echo 00 > root-ca.crlnum
openssl rand -hex 16 > root-ca.serial
```

This is a sample root-ca.cnf file.   You can replace any **example.net** entries with your own entries.  For us I just made up a domain like **private.ossim.io** and generated CERTS for each node in that DNS lookup.  Example:  **node1.private.ossim.io**

Note:  If you already have a way to sign RSA Keys with a root CA then you can ignore creating you r own CA and skip to the Certificate Signing Request section.

```text
#
# OpenSSL configuration for the Root Certification Authority.
#

#
# This definition doesn't work if HOME isn't defined.
CA_HOME                 = .
RANDFILE                = $ENV::CA_HOME/private/.rnd

#
# Default Certification Authority
[ ca ]
default_ca              = root_ca

#
# Root Certification Authority
[ root_ca ]
dir                     = $ENV::CA_HOME
certs                   = $dir/certs
serial                  = $dir/root-ca.serial
database                = $dir/root-ca.index
new_certs_dir           = $dir/newcerts
certificate             = $dir/root-ca.cert.pem
private_key             = $dir/private/root-ca.key.pem
default_days            = 1826 # Five years
crl                     = $dir/root-ca.crl
crl_dir                 = $dir/crl
crlnumber               = $dir/root-ca.crlnum
name_opt                = multiline, align
cert_opt                = no_pubkey
copy_extensions         = copy
crl_extensions          = crl_ext
default_crl_days        = 180
default_md              = sha256
preserve                = no
email_in_dn             = no
policy                  = policy
unique_subject          = no

#
# Distinguished Name Policy for CAs
[ policy ]
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = supplied
organizationalUnitName  = optional
commonName              = supplied

#
# Root CA Request Options
[ req ]
default_bits            = 4096
default_keyfile         = private/root-ca.key.pem
encrypt_key             = yes
default_md              = sha256
string_mask             = utf8only
utf8                    = yes
prompt                  = no
req_extensions          = root-ca_req_ext
distinguished_name      = distinguished_name
subjectAltName          = @subject_alt_name

#
# Root CA Request Extensions
[ root-ca_req_ext ]
subjectKeyIdentifier    = hash
subjectAltName          = @subject_alt_name

#
# Distinguished Name (DN)
[ distinguished_name ]
organizationName        = example.net
commonName              = example.net Root Certification Authority

#
# Root CA Certificate Extensions
[ root-ca_ext ]
basicConstraints        = critical, CA:true
keyUsage                = critical, keyCertSign, cRLSign
nameConstraints         = critical, @name_constraints
subjectKeyIdentifier    = hash
subjectAltName          = @subject_alt_name
authorityKeyIdentifier  = keyid:always
issuerAltName           = issuer:copy
authorityInfoAccess     = @auth_info_access
crlDistributionPoints   = crl_dist

#
# Intermediate CA Certificate Extensions
[ intermed-ca_ext ]
basicConstraints        = critical, CA:true, pathlen:0
keyUsage                = critical, keyCertSign, cRLSign
subjectKeyIdentifier    = hash
subjectAltName          = @subject_alt_name
authorityKeyIdentifier  = keyid:always
issuerAltName           = issuer:copy
authorityInfoAccess     = @auth_info_access
crlDistributionPoints   = crl_dist

#
# CRL Certificate Extensions
[ crl_ext ]
authorityKeyIdentifier  = keyid:always
issuerAltName           = issuer:copy

#
# Certificate Authorities Alternative Names
[ subject_alt_name ]
URI                     = http://ca.example.net/
email                   = certmaster@example.net

#
# Name Constraints
[ name_constraints ]
permitted;DNS.1         = example.net
permitted;DNS.2         = example.org
permitted;DNS.3         = lan
permitted;DNS.4         = onion
permitted;email.1       = example.net
permitted;email.2       = example.org

#
# Certificate download addresses for the root CA
[ auth_info_access ]
caIssuers;URI           = http://ca.example.net/certs/example.net_Root_Certification_Authority.cert.pem

#
# CRL Download address for the root CA
[ crl_dist ]
fullname                = URI:http://ca.example.net/crl/example.net_Root_Certification_Authority.crl

# EOF
```

We will set the OPENSSL_CONF to the root directory where our root-ca.cnf and run our cert generation process in that directory:

```bash
export OPENSSL_CONF=./root-ca.cnf
```

**Generate CSR and new Key**

```bash
openssl req -new -out root-ca.req.pem
```

You will find the key in **private/root-ca.key** and the CSR in **root-ca.csr**.

protect the private key:

```bash
chmod 400 private/root-ca.key.pem
```

```bash
openssl req -new -key private/root-ca.key.pem -out root-ca.req.pem
```

**Generate CSR from existing Key**

```bash
openssl req -new -key private/root-ca.key.pem -out root-ca.req.pem
```

**Show the CSR**

You can peek in to the CSR:

```bash
openssl req -verify -in root-ca.req.pem -noout -text -reqopt no_version,no_pubkey,no_sigdump -nameopt multiline
```

**Self-Signing the Root Certificate**

If everything looks ok, self-sign your own request:

```bash
openssl rand -hex 16 > root-ca.serial
openssl ca -selfsign -in root-ca.req.pem -out root-ca.cert.pem -extensions root-ca_ext \
    -startdate `date +%y%m%d000000Z -u -d -1day` \
    -enddate `date +%y%m%d000000Z -u -d +10years+1day`
```

The signature will be valid for the next ten years.

View it with the following command:

```bash
openssl x509 -in ./root-ca.cert.pem \
    -noout -text \
    -certopt no_version,no_pubkey,no_sigdump \
    -nameopt multiline
```

You can verify if it will be recognized as valid:

```bash
openssl verify -verbose -CAfile root-ca.cert.pem \
    root-ca.cert.pem
```

output:
  root-ca.cert.pem: OK

**Create Each Server Certificate**

First create a file called san.cnf.

```Text
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn
[dn]
C = US
ST = FL
[req_ext]
subjectAltName = @alt_names
```

For this example I will use names ipsec1.private.ossim.io.  Please change accordingly for your distribution.

```bash
## Unset the Config file
unset OPENSSL_CONF
export SERVERS="ipsec1.private.ossim.io ipsec2.private.ossim.io"
# Now generate your certs for each server

echo "[req]" > san.cnf
echo "default_bits = 2048" >> san.cnf
echo "prompt = no" >> san.cnf
echo "default_md = sha256" >> san.cnf
echo "req_extensions = req_ext" >> san.cnf
echo "distinguished_name = dn" >> san.cnf
echo "[dn]" >> san.cnf
echo "C = US" >> san.cnf
echo "ST = FL" >> san.cnf
echo "O = Maxar, Inc." >> san.cnf

for server in $SERVERS ; do
  openssl genrsa -out newcerts/$server.key 2048;
  openssl req -new -sha256 -key newcerts/$server.key -reqexts alt_names -config <(cat san.cnf <(printf "CN = ${server}\n[alt_names]\nsubjectAltName = DNS:$server")) -out $server.csr;
  openssl x509 -req -in $server.csr -CA root-ca.cert.pem -CAkey private/root-ca.key.pem -CAcreateserial -out newcerts/$server.crt -days 500 -sha256;
  openssl x509 -in newcerts/$server.crt -text -noout;
  rm -f $server.csr;
  openssl pkcs12 -export -in newcerts/$server.crt -name $server -inkey newcerts/$server.key  -certfile root-ca.cert.pem -passout pass: -out newcerts/$server.p12
done
```