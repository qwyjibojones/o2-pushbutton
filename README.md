This contains a docker-compose file and application.yml files to support a single, pushbutton-based O2 instance.

## Requirements

This does not contain all necessary files, such as the expected elevation data and imagery.

### Elevation Data

The elevation data can be found at: https://s3.amazonaws.com/o2-test-data/elevation/dted/dted-elevation.tgz

It will need to be extracted with `tar -xzf`, and will produce an `elevation` folder.
This folder needs to be present in this project folder, next to the `docker-compose.yml` file.
Docker-compose will then volume this folder into one of the containers on start.

### Imagery
The imagery that has been loaded into the database can be found at: https://s3.amazonaws.com/o2-test-data/sanfrancisco.tgz

It will need to be extracted with `tar -xzf`, and will produce an `sanfrancisco` folder.
This folder needs to be present in this project folder, next to the `docker-compose.yml` file.
Docker-compose will then volume this folder into one of the containers on start.

## Running

To run O2 in the foreground, run `docker-compose up`

To run O2 in the background, run `docker-compose up -d`

## Using the Deployment

The deployment can be reached at https://localhost/omar-ui
