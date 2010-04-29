import ipipe
import Queue

from pycanlib import CAN

class CANReader(CAN.Listener):
    def __init__(self):
        self.__msg_queue = Queue.Queue(0)

    def on_message_received(self, msg):
        self.__msg_queue.put_nowait(msg)

    def on_status_change(self, timestamp, old_status, new_status):
        pass

    def get_message(self):
        try:
            return self.__msg_queue.get(timeout=1)
        except Queue.Empty:
            return None

class ReadCAN(ipipe.Table):

    def __init__(self, channel, speed, tseg1, tseg2, sjw, no_samp):
        ipipe.Table.__init__(None)
        self.__bus = CAN.Bus(channel=channel, speed=speed, tseg1=tseg1, tseg2=tseg2, sjw=sjw, no_samp=no_samp)
        self.__reader = CANReader()
        self.__bus.add_listener(self.__reader)
        self.__bus.enable_callback()

    def __iter__(self):
        try:
            while True:
                _msg = self.__reader.get_message()
                if _msg != None:
                    yield _msg
        except KeyboardInterrupt:
            pass
        finally:
            self.__bus.shutdown()
