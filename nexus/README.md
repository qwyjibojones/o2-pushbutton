# Capabilities

Nexus is a repository manager which stores artifacts/binaries/releases. It can function as a maven repository, yum repository, docker registry, and more.

## Using Nexus as a Yum repository

You can upload RPM files to Yum to self-host or you can create proxies in Nexus to mirror existing Yum repositories.
If using `nexus.ossim.io`, you can use the file `nexus.repo` in this directory. 
That file points to the `all-yum-repos` repository in Nexus which mirrors all the standard CentOS repositories and our Ossim repositories.
Therefore, once nexus.repo is used, the other files in `/etc/yum.repos.d/` can safely be deleted. 

# Responsibilities

Nexus is the de facto location for O2 project dependency related artifacts except docker images, which are stored in Quay. 
Specifically, Nexus serves as the maven repository (used by Gradle) and Yum repository.
 

# Organization

Nexus maintains three types of assets/components: Hosted, Proxy, and Group; the Group type is no more than a collection of Hosted and Proxy type assets.
Hosted assets are stored directly on the Nexus server.
Proxied assets are stored elsewhere and accessed through Nexus, and are subsequently cached on Nexus.


# Using nexus.ossim.io

`ossimlabs` is a Hosted repository where we publish our maven packages.
`all-repos` is a group of all maven repositories, including `ossimlabs`.
`all-yum-repos` is a group of centos mirrors, and ossim mirrors. 

# Creating a Nexus Instance

Single command: `docker run -d -p 8081:8081 --name nexus sonatype/nexus3`

Or you can run `docker-compose` on the yaml file in this directory.