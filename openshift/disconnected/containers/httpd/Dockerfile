FROM centos:latest
ENV HOME=/home/omar
USER root
RUN useradd -u 1001 -r -g 0 --create-home -d $HOME -s /sbin/nologin -c 'Default Application User' omar && \
    mkdir -p $HOME && \
    yum -y install hostname httpd gettext wget unzip nss_wrapper mod_ssl && yum clean all && \
    setcap cap_net_bind_service+ep /usr/sbin/httpd && \
    setcap cap_net_bind_service+ep /usr/sbin/apachectl&& \
    mkdir /etc/ssl/server-certs && \
    mkdir /etc/httpd/crl && \
    chmod 774 /usr/share/httpd && \
    chmod 774 /var/run/httpd && \
    chown 1001:0 /run/httpd && \
    chown 1001:0 /var/log/httpd && \
    chmod 774 /var/log/httpd && \
    chmod g+s /var/run/httpd && \
    ln -sf /proc/self/fd/1 /var/log/httpd/access_log && \
    ln -sf /proc/self/fd/1 /var/log/httpd/error_log && \
    ln -sf /proc/self/fd/1 /var/log/httpd/ssl_access_log && \
    ln -sf /proc/self/fd/1 /var/log/httpd/ssl_request_log && \
    ln -sf /proc/self/fd/1 /var/log/httpd/ssl_error_log && \
    find /usr/share/httpd -type d -exec chmod g+xws {} \; && \
    find /usr/share/httpd -type f -exec chmod g+rw {} \; && \
    find /etc/httpd -type d -exec chmod g+rw {} \; && \
    find /etc/pki -type d -exec chmod g+xws {} \; && \
    find /etc/pki -type f -exec chmod g+rw {} \; && \
    chown -R 1001:0 /usr/share/httpd && \
    chown -R 1001:0 /etc/httpd && \
    chown -R 1001:0 /etc/pki && \
    chown -R 1001:0 /etc/ssl&& \
    find $HOME -type d -exec chmod g+xws {} \; && \
    find $HOME -type f -exec chmod g+rw {} \; && \
    chown -R 1001:0 $HOME && \
    chmod 777 $HOME && \
    chown -R 1001:0 $HOME 
COPY run-httpd.sh $HOME/run-httpd.sh
RUN  chmod -v +x $HOME/run-httpd.sh
WORKDIR $HOME
EXPOSE 80 443
USER 1001
CMD ./run-httpd.sh
    