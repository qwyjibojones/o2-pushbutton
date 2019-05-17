FROM centos:latest
ENV HOME=/home/ansible
RUN  useradd -u 1001 -r -g 0 --create-home -d $HOME -s /sbin/nologin -c 'Default Application User' ansible && \
    yum install -y epel-release && yum clean all &&\
    yum install -y ansible openssh openssh-clients git curl wget awscli

WORKDIR $HOME
USER 1001
