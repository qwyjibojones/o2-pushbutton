#!/usr/bin/env bash

for i in {1..19}
do
    scp *.conf lannister-node-$i:~/
    ssh lannister-node-$i "sudo cp 99-es-stack.conf /etc/sysctl.d/;sudo cp 99-es-stack-limits.conf /etc/security/limits.d/;sudo sysctl --system"
done
