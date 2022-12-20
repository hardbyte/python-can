Neousys CAN Interface
=====================

This kind of interface can be found for example on Neousys POC-551VTC
One needs to have correct drivers and DLL (Share object for Linux) from
`Neousys <https://www.neousys-tech.com/en/support-service/resources/category/299-poc-551vtc-driver>`_.

Beware this is only tested on Linux kernel higher than v5.3. This should be drop in
with Windows but you have to replace with correct named DLL

.. autoclass:: can.interfaces.neousys.NeousysBus
    :show-inheritance:
    :members:
