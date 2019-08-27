FROM centos:latest
RUN yum install -y createrepo wget centos-release-ansible26 libcap-ng-devel python-six openssl rpm-build yum-utils autoconf automake openssl-devel python-devel groff graphviz selinux-policy-devel python-sphinx python-twisted-core python-zope-interface libcap-ng-develAA libtool desktop-file-utils; \
    yum clean all
COPY rpm-repos/* /etc/yum.repos.d/
