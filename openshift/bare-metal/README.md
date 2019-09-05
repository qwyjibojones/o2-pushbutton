# OpenShift-3.11 Bare Metal Installation and Configuration

## Requirements

**Step 01.** Ensure your cluster hardware meets the following requirements. For completeness we will repeat from the Origin Documentation for 3.11 the Hardware Requirements but tailored to our CentOS7 environment.

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
  
*Notes:* It is recommended the cluster contain at least 2 masters and 2 infra nodes that route service traffic within the cluster. If resources are limited the infra support may be placed on the master nodes.  The compute nodes typically handle all the main processing pods.  The number of compute nodes will allow horizontal scaling by increasing the pod count and if the pod resources exceeds the resources of the cluster then another compute node can be added to the cluster. 
  
**Step 02.** Prepare the NPE Certificate(s) for each endpoint hosted via https. 

*Notes:* This will at a minimum be used for hawkular, and the web console. It is preferable to have a valid wildcard NPE certificate that can be used.  If this is in the format of a .p12 it needs to be converted into a pem and key without a password and have the CA available.  If the ability to use a wildcard NPE CERT that is fine.

## Ansible

**Step 03.** Locate or provision a machine that will serve to install and configure the cluster. 

*Notes:* This machine does not need to be very powerful, for it is only used for cluster configuration.  The machine will also serve up the OpenShift origin containers and the RPMS used during the installation process.  The machine uses ansible to configure the OpenShift cluster using the openshift-ansible playbooks.  If resources are limited, use the node that will be dedicated to the OpenShift master as the ansible machine.  It is best to have a separate ansible machine dedicated to the configuration of the cluster, so if the cluster needs to be destroyed and re-installed, you still have your configuration machine in tact.

**Step 04.** Install the necessary dependencies:
```bash
sudo yum install -y ansible
sudo yum install -y centos-release-ansible26
sudo yum install -y git 
sudo yum install -y httpd-tools 
sudo yum install -y java-1.8.0-openjdk-headless
sudo yum install -y pyOpenSSL 
sudo yum install -y python-passlib 
```

*Notes:* For disconnected environments, all dependency RPMs need to be in a common repo and have a repo file under `/etc/yum.repo.d/` directory pointing to the common yum repository. Obviously, git can be ignored in this case. At the time of writing this document we are using ansible version **2.7.10**.  

**Step 05.** On an internet connected machine, checkout out the the openshift-ansible playbooks.
```bash
cd ~
git clone https://github.com/openshift/openshift-ansible.git
cd ~/openshift-ansible
git checkout release-3.11
```

*Notes:* For disconnected environments, make this repository available. 

### SSH Keys and Config

**Step 06.** Create an SSH key to allow the ansible machine to communicate with the rest of the cluster:
```bash
mkdir ~/.ssh;chmod 700 ~/.ssh
ssh-keygen -f ~/.ssh/os-config-key-rsa -t rsa -b 4096
ssh-copy-id -i ~/.ssh/os-config-key-rsa user@host
```

*Notes:* The preferred way is to create an ssh key without a password.  If a password is added to the ssh key, use an ssh-agent on the ansible machine. 

**Step 07.** Copy the ssh keys to all nodes in the cluster. 

*Notes:* It is important to note that the **ssh user must have sudo rights** on each node, for the ansible scripts will install items that require sudo privileges.  If the **keys are password protected** then make sure the ssh-agent is running on the ansible machine and then add the key.

**Step 08.** Create `~/.ssh/config` on the ansible machine, listing all the nodes in the cluster: 
```config
Host <master nodes(s)>
  User centos
  IdentityFile ~/.ssh/os-config-key-rsa
Host <infra node(s)>
  User centos
  IdentityFile ~/.ssh/os-config-key-rsa
Host <compute node(s)>
  User centos
  IdentityFile ~/.ssh/os-config-key-rsa
Host <load balancer(s)>
  User centos
  IdentityFile ~/.ssh/os-config-key-rsa
```

**Step 09.** Change the permissions on the config file:
```bash
chmod 600 ~/.ssh/config
```

**Step 10.** Setup NetworkManager and python ssl on all nodes:

```bash
ssh <node-dns-or-ip> "sudo yum install -y python-passlib java-1.8.0-openjdk-headless NetworkManager pyOpenSSL;sudo systemctl enable NetworkManager;sudo systemctl start NetworkManager"
```

*Note*: When the installation is started and messages appear in the form  `RETRYING: Wait for the ServiceMonitor CRD to be created` make sure ip forwarding is enabled on all nodes see [Ip Forwarding Must Be Enabled](#ip-forwarding-must-be-enabled) section on how to set the value.

**Step 11.** If a gluster cluster needs to be configured for openshift dynamic provisioning support then run the following script:

```bash
ssh <gluster-dns-or-ip> "sudo yum install -y python-passlib java-1.8.0-openjdk-headless NetworkManager pyOpenSSL; sudo systemctl enable NetworkManager; sudo systemctl start NetworkManager"
```
*Notes:* The gluster cluster should have un-allocated disks and OpenShift installs heketi to add a restful interface for dynamically provisioning space from the gluster cluster.

### Dynamic Provisioning with Gluster

**Step 12.** If provisioning with Gluster, modify the inventory file appropriately: 

```config
openshift_storage_glusterfs_is_native=true
openshift_storage_glusterfs_heketi_is_native=true
openshift_storage_glusterfs_name="dynamic"
```

*Notes:* For the gluster ansible scripts to work, please make sure you have the latest CentOS7 and updates installed on your gluster nodes.  We will show the dynamic provisioning via heketi.  The dynamic provisioning is facilitated through heketi and will carve out volumes from the gluster cluster on demand.  At the time of writing this document the version of CentOS that we know worked with the configuration setup is **CentOS Linux release 7.6.1810 (Core)**.  Note, when the openshift installation gets to heketi and it loads the topology it seems to take a while, so please be patient.

A gluster server is installed on every node listed in the **[glusterfs]** section.

The storage class reference name used will be prefixed with glusterfs.  the keyword **openshift_storage_glusterfs_name** will indicate that a storage class reference **glusterfs-dynamic** can be used to reference the dynamic provisioner.

So the gluster will not have any worker pods scheduled to it, we will redefined the node_groups and add another group called **node-config-compute-storage**.  At the time of writing this document we have not found a way to append to the current list of node groups so we have to specify all the groups we will need in the current list plus any additional groups.  We can make this much more readable by using an external variables file and cut and paste the values from the main.yml and put into our YAML inventory vars file.   In this example we show the format in the inventory file.  

```config
openshift_node_groups=[{'name': 'node-config-master', 'labels': ['node-role.kubernetes.io/master=true']}, {'name': 'node-config-infra', 'labels': ['node-role.kubernetes.io/infra=true']}, {'name': 'node-config-compute', 'labels': ['node-role.kubernetes.io/compute=true']}, {'name': 'node-config-compute-storage', 'labels': ['node-role.kubernetes.io/compute-storage=true']}]
```

We can override the variable without editing the scripts but the original list can be found under the file **roles/openshift_facts/defaults/main.yml** relative from the the top level openshift-ansible directory.  Any node group can be copied out and added to the list.

### Configure the Nodes in the Cluster

**Step 12.** Edit the openshift inventory file:  
```bash
cp o2-pushbutton/openshift/bare-metal/openshift-inventory-sample ~/openshift-inventory
vi ~/openshift-inventory
```

*Note:* If you only have a couple of machines to use for an OpenShift cluster then you can merge the definitions so they share machines.  For example,  you can have your master node, infra, and etcd all on one node and use the other node for compute only.  

**Step 13.** Let ansible configure the cluster: 
```bash
cd ~/openshift-ansible
ansible-playbook -i ~/openshift-inventory playbooks/prerequisites.yml
ansible-playbook -i ~/openshift-inventory playbooks/deploy_cluster.yml
```
*Notes:* Use the `playbooks/adhoc/uninstall.yml` playbook liberally as it may take a few times to properly configure the cluster. 

**Step 14.** Setup the Security Context for the cluster to allow things to run as any user:

```bash
oc login -u system:admin
oc edit scc privileged
```
```yaml
allowPrivilegeEscalation: true
allowPrivilegedContainer: true

runAsUser:
  type: RunAsAny
```

**Step 15.** Edit the restricted scc:

```bash
oc login -u system:admin
oc edit scc restricted
```
```yaml
allowPrivilegeEscalation: true
allowPrivilegedContainer: true

defaultAddCapabilities:
- SYS_ADMIN

runAsUser:
  type: RunAsAny
```

*Notes:* The defaultAddCapabilities might be set to NULL initially.  This is needed for some of the pods that wish to have s3 mounting via goofys.

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

### Ip Forwarding Must Be Enabled

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
