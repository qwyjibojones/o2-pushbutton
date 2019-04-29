#!/bin/sh
if [ $# -lt 2 ] ;  then
  echo "Need to supply <image> <script> [<args>]"
  exit 1
fi
docker run -it --net=host --ipc host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" --rm -w /home/omar/ossimlabs --mount type=bind,source=$PWD,target=/home/openshift $*

