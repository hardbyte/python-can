Howto
=====


Interface test
------------------------

1. Implement a interface.
#. Create test file within the folder ``test/`` with the name interface\_[INTERFACE NAME]\_test.py (for example
   ``test/interface_simpleserial_test.py``).
#. Create a test case that inherits from ``GenericInterfaceTest`` and ``unittest.TestCase``.
#. Mock underlying connections / devices. The mock must simulate the underlying connection / device and
   implement all necessary functions of the connection / device, like timeouts and sending and receiving. In the test
   cases a message will be send and receive over the bus and check if the content is the same. For timeout tests the
   variable ``test.interface_test.sleep_time_rx_tx`` will be used from the test cases. The variable should be used in
   the mocks as a virtual sleep time to simulate timeouts.
#. Add setup and teardown for the mock and interface.
#. Add skip annotation (@skip_interface) in the file ``test/interface_test.py`` for all tests to be skipped.
#. Implement interface specific tests in the file interface\_[INTERFACE NAME]\_test.py.

Assumptions:
~~~~~~~~~~~~
* The default timeout of the bus is 0.1 seconds.

Implementation example:
~~~~~~~~~~~~~~~~~~~~~~~
``test/interface_simpleserial_test.py``:

.. literalinclude:: ../test/interface_simpleserial_test.py
    :language: python
    :linenos:

Skip a test example:
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @skip_interface(SlcanBus, 'function not implemented')
    def test_tx_reset_timeout(self):
        """
        Tests reset of the timeout after a timeout is set with an parameter on send
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        self.bus.send(Message(timestamp=1), 0.12)
        with self.assertRaises(CanError):
            self.bus.send(Message(timestamp=1))