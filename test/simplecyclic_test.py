from time import sleep
import unittest
import can


class SimpleCyclicSendTaskTest(unittest.TestCase):

    def test_cycle_time(self):
        msg = can.Message(extended_id=False, arbitration_id=0x100, data=[0,1,2,3,4,5,6,7])
        bus = can.interface.Bus(bustype='virtual')
        bus2 = can.interface.Bus(bustype='virtual')
        task = bus.send_periodic(msg, 0.01, 1)
        self.assertIsInstance(task, can.broadcastmanager.CyclicSendTaskABC)

        sleep(1.5)
        size = bus2.queue.qsize()
        print(size)
        # About 100 messages should have been transmitted
        self.assertTrue(90 < size < 110)
        last_msg = bus2.recv()
        self.assertEqual(last_msg, msg)

        bus.shutdown()
        bus2.shutdown()


if __name__ == '__main__':
    unittest.main()
