# Synchronize the RPM distribution OpenShift Origin Version 3.11

**Step 01** Build the synchronization image: `./build-sync.sh`

*Notes:* We have a [Dockerfile](./Dockerfile) that we use to build a synchronization image so we can download and synchronize the RPM repo from the Origin 3.11 repo. It is assumed that you have docker already running. This script will

* Pull a CentOS latest distribution
* Make sure the reposync RPM is installed
* Copy the [CentOS-OpenShift-Origin311.repo](./rpm-repos/CentOS-OpenShift-Origin311.repo) repo under rpm-repos the /etc/yum.repos.d/ location
* Tag a new base image called os-sync where "os" stands for OpenShift

**Step 02** Cache all the rpms: `./sync-repo.sh /data/disconnected/rpms`

*Notes:* This will call a script that runs the docker and then executes the reposync command against the repo ID centos-openshift-origin311. The results of running the build and then synchronize will give you a downloaded copy of the all the latest RPM's for this OpenShift version into the `/data.disconnected/rpms`.
