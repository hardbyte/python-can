#!/bin/bash

# Used by .travis.yml

sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
