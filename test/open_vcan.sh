#!/bin/bash

# Used by .travis.yml (which is executed with sudo privileges)

modprobe vcan
ip link add dev vcan0 type vcan
ip link set up vcan0 mtu 72
ip link add dev vxcan0 type vcan
ip link set up vxcan0 mtu 72
ip link add dev slcan0 type vcan
ip link set up slcan0 mtu 72
