class BitTiming:
    """Representation of a bit timing configuration.

    The class can be constructed in various ways, depending on the information
    available or the capabilities of the interfaces that need to be supported.

    The preferred way is using bitrate, CAN clock frequency, TSEG1, TSEG2, SJW::

        can.BitTiming(bitrate=1000000, f_clock=8000000, tseg1=5, tseg2=1, sjw=1)

    If the clock frequency is unknown it may be omitted but some interfaces may
    require it.

    Alternatively the BRP can be given instead of bitrate and clock frequency but this
    will limit the number of supported interfaces.

    It is also possible specify BTR registers directly,
    but will not work for all interfaces::

        can.BitTiming(btr0=0x00, btr1=0x14)
    """

    sync_seg = 1

    def __init__(
        self,
        bitrate=None,
        f_clock=None,
        brp=None,
        tseg1=None,
        tseg2=None,
        sjw=None,
        nof_samples=1,
        btr0=None,
        btr1=None,
    ):
        """
        :param int bitrate:
            Bitrate in bits/s.
        :param int f_clock:
            The CAN system clock frequency in Hz.
            Usually the oscillator frequency divided by 2.
        :param int brp:
            Bit Rate Prescaler. Prefer to use bitrate and f_clock instead.
        :param int tseg1:
            Time segment 1, that is, the number of quanta from (but not including)
            the Sync Segment to the sampling point.
        :param int tseg2:
            Time segment 2, that is, the number of quanta from the sampling
            point to the end of the bit.
        :param int sjw:
            The Synchronization Jump Width. Decides the maximum number of time quanta
            that the controller can resynchronize every bit.
        :param int nof_samples:
            Either 1 or 3. Some CAN controllers can also sample each bit three times.
            In this case, the bit will be sampled three quanta in a row,
            with the last sample being taken in the edge between TSEG1 and TSEG2.
            Three samples should only be used for relatively slow baudrates.
        :param int btr0:
            The BTR0 register value used by many CAN controllers.
        :param int btr1:
            The BTR1 register value used by many CAN controllers.
        """
        self._bitrate = bitrate
        self._brp = brp
        self._sjw = sjw
        self._tseg1 = tseg1
        self._tseg2 = tseg2
        self._nof_samples = nof_samples
        self._f_clock = f_clock

        if btr0 is not None:
            self._brp = (btr0 & 0x3F) + 1
            self._sjw = (btr0 >> 6) + 1
        if btr1 is not None:
            self._tseg1 = (btr1 & 0xF) + 1
            self._tseg2 = ((btr1 >> 4) & 0x7) + 1
            self._nof_samples = 3 if btr1 & 0x80 else 1

        if nof_samples not in (1, 3):
            raise ValueError("nof_samples must be 1 or 3")

    @property
    def nbt(self):
        """Nominal Bit Time."""
        return self.sync_seg + self.tseg1 + self.tseg2

    @property
    def bitrate(self):
        """Bitrate in bits/s."""
        if self._bitrate:
            return self._bitrate
        if self._f_clock and self._brp:
            return self._f_clock / (self._brp * self.nbt)
        raise ValueError("bitrate must be specified")

    @property
    def brp(self):
        """Bit Rate Prescaler."""
        if self._brp:
            return self._brp
        if self._f_clock and self._bitrate:
            return round(self._f_clock / (self._bitrate * self.nbt))
        raise ValueError("Either bitrate and f_clock or brp must be specified")

    @property
    def sjw(self):
        """Synchronization Jump Width."""
        if not self._sjw:
            raise ValueError("sjw must be specified")
        return self._sjw

    @property
    def tseg1(self):
        """Time segment 1.

        The number of quanta from (but not including) the Sync Segment to the sampling point.
        """
        if not self._tseg1:
            raise ValueError("tseg1 must be specified")
        return self._tseg1

    @property
    def tseg2(self):
        """Time segment 2.

        The number of quanta from the sampling point to the end of the bit.
        """
        if not self._tseg2:
            raise ValueError("tseg2 must be specified")
        return self._tseg2

    @property
    def nof_samples(self):
        """Number of samples (1 or 3)."""
        if not self._nof_samples:
            raise ValueError("nof_samples must be specified")
        return self._nof_samples

    @property
    def f_clock(self):
        """The CAN system clock frequency in Hz.

        Usually the oscillator frequency divided by 2.
        """
        if not self._f_clock:
            raise ValueError("f_clock must be specified")
        return self._f_clock

    @property
    def sample_point(self):
        """Sample point in percent."""
        return 100.0 * (self.nbt - self.tseg2) / self.nbt

    @property
    def btr0(self):
        sjw = self.sjw
        brp = self.brp

        if brp < 1 or brp > 64:
            raise ValueError("brp must be 1 - 64")
        if sjw < 1 or sjw > 4:
            raise ValueError("sjw must be 1 - 4")

        return (sjw - 1) << 6 | brp - 1

    @property
    def btr1(self):
        sam = 1 if self.nof_samples == 3 else 0
        tseg1 = self.tseg1
        tseg2 = self.tseg2

        if tseg1 < 1 or tseg1 > 16:
            raise ValueError("tseg1 must be 1 - 16")
        if tseg2 < 1 or tseg2 > 8:
            raise ValueError("tseg2 must be 1 - 8")

        return sam << 7 | (tseg2 - 1) << 4 | tseg1 - 1

    def __str__(self):
        segments = []
        try:
            segments.append(f"{self.bitrate} bits/s")
        except ValueError:
            pass
        try:
            segments.append(f"sample point: {self.sample_point:.2f}%")
        except ValueError:
            pass
        try:
            segments.append(f"BRP: {self.brp}")
        except ValueError:
            pass
        try:
            segments.append(f"TSEG1: {self.tseg1}")
        except ValueError:
            pass
        try:
            segments.append(f"TSEG2: {self.tseg2}")
        except ValueError:
            pass
        try:
            segments.append(f"SJW: {self.sjw}")
        except ValueError:
            pass
        try:
            segments.append(f"BTR: {self.btr0:02X}{self.btr1:02X}h")
        except ValueError:
            pass
        return ", ".join(segments)
