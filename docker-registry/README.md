## Role of the Docker Registry

The Docker Registry is a local database of docker images for support containerized deployments of tools such as O2.

## Creating the Docker Registry

Simple Docker container: `docker run -p 5000:5000 registry`
Via Docker Compose: `docker-compose -f registry.yml up`


### Short Example

In this example, the user pulls some image, in this case 'ubuntu,' from the global registry and pushes it to a new local registry.

```bash
$ docker pull ubuntu
$ docker tag ubuntu localhost:5000/ubuntu
$ docker push localhost:5000/ubuntu
```