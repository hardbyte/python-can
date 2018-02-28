#!/bin/bash

# Used by .travis.yml (which is executed with sudo privileges)

modprobe vcan
ip link add dev vcan0 type vcan
ip link set up vcan0
