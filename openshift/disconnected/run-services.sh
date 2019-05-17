#!/bin/bash
WORKING_DIRECTORY=$1

if [ "$WORKING_DIRECTORY" == "" ] ; then
  echo "Please pass in the working directory where the yum cache is located"
  echo "Usage:"
  echo "    $0 <working directory>"
fi

pushd $WORKING_DIRECTORY
docker run -d -p 5000:5000 --restart=always \
        --name registry \
        -v "$(pwd)"/server-certs:/certs \
        -v "$(pwd)"/registry:/var/lib/registry \
        registry
docker run -d -p 80:80 -p 443:443   --restart=always \
       --link registry:registry \
       --name httpd \
       -v $(pwd)/server-certs:/etc/ssl/server-certs \
       -v $(pwd)/rpms:/var/www/html/rpms \
       -v $(pwd)/reverse-proxy.conf:/etc/httpd/conf.d/reverse-proxy.conf \
       httpd
popd
