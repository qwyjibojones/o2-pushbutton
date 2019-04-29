# Synchronize the RPM distribution OpenShift Origin Version 3.11

We have a [Dockerfile](./Dockerfile) that we use to build a synchronization image so we can download and synchronize the RPM repo from the Origin 3.11 repo.

```bash
./build-sync.sh
./sync-repo.sh <destination-dir>
```

The **build-synch.sh** is responsible for

* Pulling a CentOS latest distribution
* Making sure the reposync RPM is installed
* Copying the Origin repo under rpm-repos the /etc/yum.repos.d/ location
* Tagging a new base image called os-sync where "os" stands for OpenShift

We then need to run the command **repo-synch.sh** to then call a script that runs the docker and then executes the reposync command with the ID centos-openshift-origin311.  

The results of running the build and then synchronize will give you a downloaded copy of the all the latest RPM's for this OpenShift version