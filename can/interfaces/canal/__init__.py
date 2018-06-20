#!/usr/bin/env python
# coding: utf-8

"""
This module exposes the CANAL backend.

This interface is for Windows only, please use socketcan on Unix/Linux.
"""

from can.interfaces.canal.canal_interface import CanalBus
from can.interfaces.canal.canal_wrapper import CanalWrapper
