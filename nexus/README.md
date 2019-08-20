# Capabilities

Nexus is a repository manager which stores artifacts/binaries/releases. It can function as a maven repository, yum repository, docker registry, and more.


# Responsibilities

Nexus is the de facto location for O2 project dependency related artifacts except docker images, which are stored in Quay. 
Specifically, Nexus serves as the maven repository (used by Gradle) and Yum repository.
 

# Organization

Nexus maintains three types of assets/components: Hosted, Proxy, and Group; the Group type is no more than a collection of Hosted and Proxy type assets.
Hosted assets are stored directly on the Nexus server.
Proxied assets are stored elsewhere and accessed through Nexus, and are subsequently cached on Nexus.


# The Shared Nexus

`ossimlabs` is a Hosted repository where we publish our maven packages.
`all-repos` is a group that encapsulates _all_ maven repositories, including `ossimlabs`.

# Creating a Nexus Instance

Single command: `docker run -d -p 8081:8081 --name nexus sonatype/nexus3`

Or you can run `docker-compose` on the yaml file in this directory.