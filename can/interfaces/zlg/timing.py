from can import BitTiming, CanInitializationError, CanBitRateError
from .vci import ZCAN_BIT_TIMING, ZCAN_DEVICE


# Official timing calculation
#   https://manual.zlg.cn/web/#/188/6981
class ZlgBitTiming(BitTiming):
    def __init__(self, device, **kwargs):
        try:
            self._device = ZCAN_DEVICE(device)
        except:
            raise CanInitializationError(f"Unsupported ZLG CAN device {device} !")
        if self._device in (
            ZCAN_DEVICE.USBCAN,
            ZCAN_DEVICE.USBCANFD_200U,
        ):
            kwargs.setdefault("f_clock", 60000000)
            self.speeds = {
                125_000: ZCAN_BIT_TIMING(tseg1=10, tseg2=2, sjw=2, brp=31),
                250_000: ZCAN_BIT_TIMING(tseg1=10, tseg2=2, sjw=2, brp=15),
                500_000: ZCAN_BIT_TIMING(tseg1=10, tseg2=2, sjw=2, brp=7),
                1_000_000: ZCAN_BIT_TIMING(tseg1=46, tseg2=11, sjw=3, brp=0),
                2_000_000: ZCAN_BIT_TIMING(tseg1=10, tseg2=2, sjw=2, brp=1),
                4_000_000: ZCAN_BIT_TIMING(tseg1=10, tseg2=2, sjw=2, brp=0),
                5_000_000: ZCAN_BIT_TIMING(tseg1=7, tseg2=2, sjw=2, brp=0),
            }
        super().__init__(**kwargs)

    def timing(self, bitrate=None, force=False) -> ZCAN_BIT_TIMING:
        if bitrate in self.speeds:
            return self.speeds[bitrate]
        elif force:
            return ZCAN_BIT_TIMING(
                tseg1=self.tseg1,
                tseg2=self.tseg2,
                sjw=self.sjw,
                brp=self.brp,
            )
        else:
            raise CanBitRateError(f"Unsupported {bitrate=}")

    @property
    def bitrates(self) -> list[int]:
        return self.speeds.keys()
