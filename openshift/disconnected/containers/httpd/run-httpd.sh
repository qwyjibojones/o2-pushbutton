#
# Accepts the following ENV variables
# CRL_HOME location where the crl lists are located
#          It will create appropriate hash files.  Defaults
#          /etc/httpd/crl
# 
#

#!/bin/bash
# Checks that a reverse-proxy.conf file was passed in
# If so, copies that file to the httpd/conf.d folder so that httpd uses it
# If not, defaults to the conf file that already exists on the Docker container
# if [ -e "$OMAR_WEB_PROXY_CONF" ] ; then
#   cp $OMAR_WEB_PROXY_CONF /etc/httpd/conf.d/reverse-proxy.conf
#   echo "reverse-proxy config file mounted at $OMAR_WEB_PROXY_CONF, copying to /etc/httpd/conf.d/reverse-proxy.conf"
# else
#   echo "No reverse-proxy config file provided, using container default!"
# fi
# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container.  httpd won't start correctly
# if it thinks it is already running.
rm -rf /run/httpd/* /tmp/httpd*
if [ -z $HOME ] ; then
   export HOME=/home/omar
fi
if [ ! -z "${AWS_ACCESS_KEY}" ] ; then
  export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY}
fi

if [ ! -z "${AWS_SECRET_KEY}" ] ; then
  export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_KEY}
fi
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

##
# Cat and delete the entry that starts with omar from
# the password file and copy it to /tmp
# and add the omar user with the random user id
#
if [ -f /etc/passwd ] ; then
  cat /etc/passwd | sed '/^omar/d' > /tmp/passwd
  echo omar:x:$USER_ID:$GROUP_ID:Default Application User:$HOME:/sbin/nologin >> /tmp/passwd
fi

export LD_PRELOAD=/usr/lib64/libnss_wrapper.so
export NSS_WRAPPER_PASSWD=/tmp/passwd
export NSS_WRAPPER_GROUP=/etc/group

#
# Check defautl CRL location
#
if [ -z $CRL_HOME ] ; then
   if [ -d /etc/ssl/crl ] ; then
     export CRL_HOME=/etc/ssl/crl
   fi
fi

# If the crl directory exists create the proper hash 
# files for revocation path
#
if [ ! -z $CRL_HOME ] ; then
   if [ ! -d /etc/httpd/crl ] ; then
      mkdir -p /etc/httpd/crl
   fi
   pushd /etc/httpd/crl > /dev/null
   for x in `find $CRL_HOME -name "*.crl"` ; do 
     ln -s $x `openssl crl -noout -hash -in $x`.r0 2>/dev/null
   done
   popd > /dev/null
fi
if [ -z "${MOUNT_POINT}" ] ; then
  export MOUNT_POINT=/s3
fi

if [ -z "${GOOFY_OPTS}" ] ; then
   GOOFY_OPTS="-o allow_other"
fi

# force to forground
#  we are taking a comma separated list of buckets in the form of
#  AWS  <bucket>:<prefix-path>,.....
#  where :<prefix-path> is optional.  
#  we will mount to the location <mount-point>/<prefix-path>
# 
GOOFY_OPTS="-f ${GOOFY_OPTS}"
if [ ! -z "${BUCKETS}" ] ; then
  SPLIT_BUCKET=${BUCKETS//\,/ }
  
  for BUCKET in ${SPLIT_BUCKET} ; do
    BUCKET_PATH="${MOUNT_POINT}/${BUCKET//://}"
    mkdir -p $BUCKET_PATH
    goofys ${GOOFY_OPTS} ${BUCKET} ${BUCKET_PATH} &
  done
fi

exec /usr/sbin/apachectl -DFOREGROUND
