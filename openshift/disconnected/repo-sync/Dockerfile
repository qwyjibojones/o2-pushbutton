FROM centos:latest
RUN yum install -y createrepo yum-utils; \
    yum clean all
COPY rpm-repos/* /etc/yum.repos.d/
