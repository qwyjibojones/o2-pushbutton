This directory is includes materials for installing a Jenkins instance in OpenShift.
It is currently just this README file, but in the future it may also include scripts
to automate the process.

1. Attach a volume to the NFS
  * Make EBS volume
  * Attach volume to the FNS
  * Make a filesystem on the mountpoint: `mkfs -t ext4 /dev/x...`
  * Create the mount point target `mkdir /mnt/...`
  * Add the mount point to /etc/fstab
  * Mount all definitions in fstab: `mount -a`
  * Expose the mounted dir by exiting /etc/exports
  * Restart the nfs mounts: `systemctl restart nfs`

1. Go to the 'devops' project, select the CI/CD tab, and click on the first 'Jenkins' application. Click the 'Next' button.

1. Deploy the jenkins-pv using the jenkins-pv.json template

1. Deploy the jenkins service using the jenkins-persistent-template.json

1. Once the node is up, go to it at https://jenkins-devops.ossim.io, log in with your openshift credentials, and click 'Allow selected permissions'. After a bit, you should be redirected to the home page of Jenkins. If this has not happened after a couple minutes, refresh the page.

1. The Jenkins instance will need credentials added, as described in ./credentials-list.txt

1. Install the plugins, as described in ./plugins-list.txt

1. Add the views, which can be found in the config.xml file, between the <views> and </views> tags

1. Set up the AWS EC2 nodes

1. Run the ossim-ci pipeline to generate build artifacts
