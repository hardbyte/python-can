

class BitTiming:

    # Is this always 1?
    sync_seg = 1

    def __init__(
        self,
        bitrate=None,
        brp=None,
        sjw=None,
        tseg1=None,
        tseg2=None,
        nof_samples=1,
        f_clock=None,
        btr0=None,
        btr1=None
    ):
        if brp is not None and (brp < 1 or brp > 64):
            raise ValueError("brp must be 1 - 64")
        if sjw is not None and (sjw < 1 or sjw > 4):
            raise ValueError("sjw must be 1 - 4")
        if tseg1 is not None and (tseg1 < 1 or tseg1 > 16):
            raise ValueError("tseg1 must be 1 - 16")
        if tseg2 is not None and (tseg2 < 1 or tseg2 > 8):
            raise ValueError("tseg2 must be 1 - 8")
        if nof_samples is not None and nof_samples not in (1, 3):
            raise ValueError("nof_samples must be 1 or 3")
        if btr0 is not None and (btr0 < 0 or btr0 > 255):
            raise ValueError("btr0 must be 0 - 255")
        if btr1 is not None and (btr1 < 0 or btr1 > 255):
            raise ValueError("btr1 must be 0 - 255")

        self._bitrate = bitrate
        self._brp = brp
        self._sjw = sjw
        self._tseg1 = tseg1
        self._tseg2 = tseg2
        self._nof_samples = nof_samples
        self._f_clock = f_clock
        self._btr0 = btr0
        self._btr1 = btr1

    @property
    def nbt(self):
        return self.sync_seg + self.tseg1 + self.tseg2

    @property
    def bitrate(self):
        if self._bitrate:
            return self._bitrate
        raise ValueError("bitrate must be specified")

    @property
    def brp(self):
        if self._brp:
            return self._brp
        return (2 * self.bitrate * self.nbt) // self.f_clock

    @property
    def sjw(self):
        if not self._sjw:
            raise ValueError("sjw must be specified")
        return self._sjw

    @property
    def tseg1(self):
        if not self._tseg1:
            raise ValueError("tseg1 must be specified")
        return self._tseg1

    @property
    def tseg2(self):
        if not self._tseg2:
            raise ValueError("tseg2 must be specified")
        return self._tseg2

    @property
    def nof_samples(self):
        if not self._nof_samples:
            raise ValueError("nof_samples must be specified")
        return self._nof_samples

    @property
    def f_clock(self):
        if not self._f_clock:
            raise ValueError("f_clock must be specified")
        return self._f_clock

    @property
    def btr0(self):
        if self._btr0 is not None:
            return self._btr0
        btr0 = (self.sjw - 1) << 5
        btr0 |= self.brp - 1
        return btr0

    @property
    def btr1(self):
        if self._btr1 is not None:
            return self._btr1
        sam = 1 if self.nof_samples == 3 else 0
        btr1 = sam << 7
        btr1 |= (self.tseg2 - 1) << 4
        btr1 |= self.tseg1 - 1
        return btr1

    @property
    def btr(self):
        return self.btr0 << 8 | self.btr1
