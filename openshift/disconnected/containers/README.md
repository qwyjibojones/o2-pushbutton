# Containers

## Build & Bundle

**Step 01** Build the docker containers: `./build-images.sh`

*Notes:* Although the registry Dockerfile is no more than a pointer to the docker hub registry:2 location, we supplied the docker file for completeness.

**Step 02** Bundle the docker containers: `./bundle-images.sh /data/disconnected/`
*Notes:* The output must have a trailing slash. If this is left off then it will output to the current directory.


## Download Container Dependencies

**Step 03** Create a directory for our cache: `mkdir /data/disconnected/registry`

**Step 04** Run a local registry as a docker container: `docker run -d -p 5000:5000 --restart=always --name registry -v /data/disconnected/registry:/var/lib/registry registry`

*Notes:* This will mount the directory `/data/disconnected/registry` to the container `/var/lib/registry`.

**Step 05** Run the shell script to download the images and push to your local registry: `./pull-okd-311-images.sh`

