Sometimes it may be necessary to view code/repositories with an interface. 
In such cases, we provide [Gogs](https://gogs.io/) as a lightweight alternative to GitHub.

### Creating a Gogs Docker Container

```bash
# Pull image from Docker Hub.
$ docker pull gogs/gogs

# Create local directory for volume.
$ mkdir -p /var/gogs

# Use `docker run` for the first time.
$ docker run --name=gogs -p 10022:22 -p 10080:3000 -v /var/gogs:/data gogs/gogs

# Use `docker start` if you have stopped it.
$ docker start gogs
```

### Creating a Gogs Service using Docker-Compose

We have also included a docker-compose file to capture the above configuration (port and volume mappings).
Create the service with `docker-compose -f gogs.yml up`.