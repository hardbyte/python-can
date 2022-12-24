from typing import List, Mapping, Iterator, cast

from can.typechecking import BitTimingFdDict, BitTimingDict


class BitTiming(Mapping):
    """Representation of a bit timing configuration for a CAN 2.0 bus.

    The class can be constructed in multiple ways, depending on the information
    available. The preferred way is using bitrate, CAN clock frequency, tseg1, tseg2 and sjw::

        can.BitTiming(bitrate=1_000_000, f_clock=8_000_000, tseg1=5, tseg2=1, sjw=1)

    It is also possible to specify BTR registers::

        can.BitTiming.from_registers(f_clock=8_000_000, btr0=0x00, btr1=0x14)

    or to calculate the timings for a given sample point::

        can.BitTiming.from_sample_point(f_clock=16_000_000, bitrate=500_000, sample_point=81.25)
    """

    def __init__(
        self,
        f_clock: int,
        bitrate: int,
        tseg1: int,
        tseg2: int,
        sjw: int,
        nof_samples: int = 1,
    ) -> None:
        """
        :param int f_clock:
            The CAN system clock frequency in Hz.
            Usually the oscillator frequency divided by 2.
        :param int bitrate:
            Bitrate in bit/s.
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

        """
        self._data: BitTimingDict = {
            "f_clock": f_clock,
            "bitrate": bitrate,
            "tseg1": tseg1,
            "tseg2": tseg2,
            "sjw": sjw,
            "nof_samples": nof_samples,
        }

        if not 5_000 <= bitrate <= 2_000_000:
            raise ValueError(f"bitrate (={bitrate}) must be in [5,000...2,000,000].")

        if not 1 <= tseg1 <= 16:
            raise ValueError(f"tseg1 (={tseg1}) must be in [1...16].")

        if not 1 <= tseg2 <= 8:
            raise ValueError(f"tseg2 (={tseg2}) must be in [1...8].")

        nbt = self.nbt
        if not 8 <= nbt <= 25:
            raise ValueError(f"nominal bit time (={nbt}) must be in [8...25].")

        brp = self.brp
        if not 1 <= brp <= 64:
            raise ValueError(f"bitrate prescaler (={brp}) must be in [1...64].")

        actual_bitrate = f_clock / (nbt * brp)
        if abs(actual_bitrate - bitrate) > bitrate / 256:
            raise ValueError(
                f"the actual bitrate (={actual_bitrate}) diverges "
                f"from the requested bitrate (={bitrate})"
            )

        if not 1 <= sjw <= 4:
            raise ValueError(f"sjw (={sjw}) must be in [1...4].")

        if sjw > tseg2:
            raise ValueError(f"sjw (={sjw}) must not be greater than tseg2 (={tseg2}).")

        if nof_samples not in (1, 3):
            raise ValueError("nof_samples must be 1 or 3")

    @classmethod
    def from_registers(
        cls,
        f_clock: int,
        btr0: int,
        btr1: int,
    ) -> "BitTiming":
        """Create a BitTiming instance from registers btr0 and btr1.

        :param int f_clock:
            The CAN system clock frequency in Hz.
            Usually the oscillator frequency divided by 2.
        :param int btr0:
            The BTR0 register value used by many CAN controllers.
        :param int btr1:
            The BTR1 register value used by many CAN controllers.
        """
        brp = (btr0 & 0x3F) + 1
        sjw = (btr0 >> 6) + 1
        tseg1 = (btr1 & 0xF) + 1
        tseg2 = ((btr1 >> 4) & 0x7) + 1
        nof_samples = 3 if btr1 & 0x80 else 1
        bitrate = f_clock // ((1 + tseg1 + tseg2) * brp)
        return cls(
            bitrate=bitrate,
            f_clock=f_clock,
            tseg1=tseg1,
            tseg2=tseg2,
            sjw=sjw,
            nof_samples=nof_samples,
        )

    @classmethod
    def from_sample_point(
        cls, f_clock: int, bitrate: int, sample_point: float = 69.0
    ) -> "BitTiming":
        """Create a BitTiming instance for a sample point.

        :param int f_clock:
            The CAN system clock frequency in Hz.
            Usually the oscillator frequency divided by 2.
        :param int bitrate:
            Bitrate in bit/s.
        :param int sample_point:
            The sample point value in percent.
        """

        if sample_point < 50.0:
            raise ValueError(f"sample_point (={sample_point}) must not be below 50%.")

        possible_solutions: List[BitTiming] = []
        for brp in range(1, 65):
            nbt = round(int(f_clock / (bitrate * brp)))
            if nbt < 8:
                break

            actual_bitrate = f_clock / (nbt * brp)
            if abs(actual_bitrate - bitrate) > bitrate / 256:
                continue

            tseg1 = int(round(sample_point / 100 * nbt)) - 1
            tseg2 = nbt - tseg1 - 1

            sjw = min(tseg2, 4)

            try:
                bt = BitTiming(
                    f_clock=f_clock,
                    bitrate=bitrate,
                    tseg1=tseg1,
                    tseg2=tseg2,
                    sjw=sjw,
                )
                if abs(bt.sample_point - sample_point) < 1:
                    possible_solutions.append(bt)
            except ValueError:
                continue

        if not possible_solutions:
            raise ValueError("No suitable bit timings found.")

        return sorted(
            possible_solutions, key=lambda x: x.oscillator_tolerance, reverse=True
        )[0]

    @property
    def nbt(self) -> int:
        """Nominal Bit Time."""
        return 1 + self.tseg1 + self.tseg2

    @property
    def bitrate(self) -> int:
        """Bitrate in bits/s."""
        return self["bitrate"]

    @property
    def brp(self) -> int:
        """Bit Rate Prescaler."""
        return int(round(self.f_clock / (self.bitrate * self.nbt)))

    @property
    def sjw(self) -> int:
        """Synchronization Jump Width."""
        return self["sjw"]

    @property
    def tseg1(self) -> int:
        """Time segment 1.

        The number of quanta from (but not including) the Sync Segment to the sampling point.
        """
        return self["tseg1"]

    @property
    def tseg2(self) -> int:
        """Time segment 2.

        The number of quanta from the sampling point to the end of the bit.
        """
        return self["tseg2"]

    @property
    def nof_samples(self) -> int:
        """Number of samples (1 or 3)."""
        return self["nof_samples"]

    @property
    def f_clock(self) -> int:
        """The CAN system clock frequency in Hz.

        Usually the oscillator frequency divided by 2.
        """
        return self["f_clock"]

    @property
    def sample_point(self) -> float:
        """Sample point in percent."""
        return 100.0 * (1 + self.tseg1) / (1 + self.tseg1 + self.tseg2)

    @property
    def oscillator_tolerance(self) -> float:
        """Oscillator tolerance in percent."""
        df_clock_list = [
            _oscillator_tolerance_condition_1(nom_sjw=self.sjw, nbt=self.nbt),
            _oscillator_tolerance_condition_2(nbt=self.nbt, nom_tseg2=self.tseg2),
        ]
        return min(df_clock_list) * 100

    @property
    def btr0(self) -> int:
        """Bit timing register 0."""
        return (self.sjw - 1) << 6 | self.brp - 1

    @property
    def btr1(self) -> int:
        """Bit timing register 1."""
        sam = 1 if self.nof_samples == 3 else 0
        return sam << 7 | (self.tseg2 - 1) << 4 | self.tseg1 - 1

    def __str__(self) -> str:
        segments = []
        try:
            segments.append(f"BR {self.bitrate} bit/s")
        except ValueError:
            pass
        try:
            segments.append(f"SP: {self.sample_point:.2f}%")
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
        try:
            segments.append(f"f_clock: {self.f_clock / 1e6:.0f}MHz")
        except ValueError:
            pass
        try:
            segments.append(f"df_clock: {self.oscillator_tolerance:.2f}%")
        except ValueError:
            pass
        return ", ".join(segments)

    def __repr__(self) -> str:
        args = ", ".join(f"{key}={value}" for key, value in self.items())
        return f"can.{self.__class__.__name__}({args})"

    def __getitem__(self, key: str) -> int:
        return cast(int, self._data.__getitem__(key))

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> Iterator[str]:
        return self._data.__iter__()


class BitTimingFd(Mapping):
    """Representation of a bit timing configuration for a CAN FD bus.

    The class can be constructed in multiple ways, depending on the information
    available. The preferred way is using bitrate, CAN clock frequency, tseg1, tseg2 and sjw
    for both the arbitration (nominal) and data phase::

        can.BitTimingFd(
            f_clock=80_000_000,
            nom_bitrate=1_000_000,
            nom_tseg1=59,
            nom_tseg2=20,
            nom_sjw=10,
            data_bitrate=8_000_000,
            data_tseg1=6,
            data_tseg2=3,
            data_sjw=2,
        )

    It is also possible to calculate the timings for a given
    pair of arbitration and data sample points::

        can.BitTimingFd.from_sample_point(
            f_clock=80_000_000,
            nom_bitrate=1_000_000,
            nom_sample_point=75.0,
            data_bitrate=8_000_000,
            data_sample_point=70.0,
        )
    """

    def __init__(
        self,
        f_clock: int,
        nom_bitrate: int,
        nom_tseg1: int,
        nom_tseg2: int,
        nom_sjw: int,
        data_bitrate: int,
        data_tseg1: int,
        data_tseg2: int,
        data_sjw: int,
    ) -> None:
        self._data: BitTimingFdDict = {
            "f_clock": f_clock,
            "nom_bitrate": nom_bitrate,
            "nom_tseg1": nom_tseg1,
            "nom_tseg2": nom_tseg2,
            "nom_sjw": nom_sjw,
            "data_bitrate": data_bitrate,
            "data_tseg1": data_tseg1,
            "data_tseg2": data_tseg2,
            "data_sjw": data_sjw,
        }

        if not 5_000 <= nom_bitrate <= 2_000_000:
            raise ValueError(
                f"nom_bitrate (={nom_bitrate}) must be in [5,000...2,000,000]."
            )

        if not 25_000 <= data_bitrate <= 8_000_000:
            raise ValueError(
                f"data_bitrate (={data_bitrate}) must be in [25,000...8,000,000]."
            )

        if data_bitrate < nom_bitrate:
            raise ValueError(
                f"data_bitrate (={data_bitrate}) must be greater than or "
                f"equal to nom_bitrate (={nom_bitrate})"
            )

        if not 2 <= nom_tseg1 <= 256:
            raise ValueError(f"nom_tseg1 (={nom_tseg1}) must be in [2...256].")

        if not 1 <= nom_tseg2 <= 128:
            raise ValueError(f"nom_tseg2 (={nom_tseg2}) must be in [1...128].")

        if not 1 <= data_tseg1 <= 32:
            raise ValueError(f"data_tseg1 (={data_tseg1}) must be in [1...32].")

        if not 1 <= data_tseg2 <= 16:
            raise ValueError(f"data_tseg2 (={data_tseg2}) must be in [1...16].")

        nbt = self.nbt
        if nbt < 8:
            raise ValueError(f"nominal bit time (={nbt}) must be at least 8.")

        dbt = self.dbt
        if dbt < 8:
            raise ValueError(f"data bit time (={dbt}) must be at least 8.")

        nom_brp = self.nom_brp
        if not 1 <= nom_brp <= 256:
            raise ValueError(
                f"nominal bitrate prescaler (={nom_brp}) must be in [1...256]."
            )

        data_brp = self.data_brp
        if not 1 <= data_brp <= 256:
            raise ValueError(
                f"data bitrate prescaler (={data_brp}) must be in [1...256]."
            )

        actual_nom_bitrate = f_clock / (nbt * nom_brp)
        if abs(actual_nom_bitrate - nom_bitrate) > nom_bitrate / 256:
            raise ValueError(
                f"the actual nominal bitrate (={actual_nom_bitrate}) diverges "
                f"from the requested bitrate (={nom_bitrate})"
            )

        actual_data_bitrate = f_clock / (dbt * data_brp)
        if abs(actual_data_bitrate - data_bitrate) > data_bitrate / 256:
            raise ValueError(
                f"the actual data bitrate (={actual_data_bitrate}) diverges "
                f"from the requested bitrate (={data_bitrate})"
            )

        if not 1 <= nom_sjw <= 128:
            raise ValueError(f"nom_sjw (={nom_sjw}) must be in [1...128].")

        if nom_sjw > nom_tseg2:
            raise ValueError(
                f"nom_sjw (={nom_sjw}) must not be greater than nom_tseg2 (={nom_tseg2})."
            )

        if not 1 <= data_sjw <= 16:
            raise ValueError(f"data_sjw (={data_sjw}) must be in [1...128].")

        if data_sjw > data_tseg2:
            raise ValueError(
                f"data_sjw (={data_sjw}) must not be greater than data_tseg2 (={data_tseg2})."
            )

    @classmethod
    def from_sample_point(
        cls,
        f_clock: int,
        nom_bitrate: int,
        nom_sample_point: float,
        data_bitrate: int,
        data_sample_point: float,
    ) -> "BitTimingFd":
        """Create a BitTimingFd instance for a given nominal/data sample point pair.

        :param int f_clock:
            The CAN system clock frequency in Hz.
            Usually the oscillator frequency divided by 2.
        :param int nom_bitrate:
            Nominal bitrate in bit/s.
        :param int nom_sample_point:
            The sample point value of the arbitration phase in percent.
        :param int data_bitrate:
            Data bitrate in bit/s.
        :param int data_sample_point:
            The sample point value of the data phase in percent.
        """
        if nom_sample_point < 50.0:
            raise ValueError(
                f"nom_sample_point (={nom_sample_point}) must not be below 50%."
            )

        if data_sample_point < 50.0:
            raise ValueError(
                f"data_sample_point (={data_sample_point}) must not be below 50%."
            )

        possible_solutions: List[BitTimingFd] = []

        for nom_brp in range(1, 257):
            nbt = round(int(f_clock / (nom_bitrate * nom_brp)))
            if nbt < 8:
                break

            actual_nom_bitrate = f_clock / (nbt * nom_brp)
            if abs(actual_nom_bitrate - nom_bitrate) > nom_bitrate / 256:
                continue

            nom_tseg1 = int(round(nom_sample_point / 100 * nbt)) - 1
            nom_tseg2 = nbt - nom_tseg1 - 1

            nom_sjw = min(nom_tseg2, 128)

            for data_brp in range(1, 257):
                dbt = round(int(f_clock / (data_bitrate * data_brp)))
                if dbt < 8:
                    break

                actual_data_bitrate = f_clock / (dbt * data_brp)
                if abs(actual_data_bitrate - data_bitrate) > data_bitrate / 256:
                    continue

                data_tseg1 = int(round(data_sample_point / 100 * dbt)) - 1
                data_tseg2 = dbt - data_tseg1 - 1

                data_sjw = min(data_tseg2, 16)

                bit_timings = {
                    "f_clock": f_clock,
                    "nom_bitrate": nom_bitrate,
                    "nom_tseg1": nom_tseg1,
                    "nom_tseg2": nom_tseg2,
                    "nom_sjw": nom_sjw,
                    "data_bitrate": data_bitrate,
                    "data_tseg1": data_tseg1,
                    "data_tseg2": data_tseg2,
                    "data_sjw": data_sjw,
                }
                try:
                    bt = BitTimingFd(**bit_timings)
                    if (
                        abs(bt.nom_sample_point - nom_sample_point) < 1
                        and abs(bt.data_sample_point - bt.data_sample_point) < 1
                    ):
                        possible_solutions.append(bt)
                except ValueError:
                    continue

        if not possible_solutions:
            raise ValueError("No suitable bit timings found.")

        # prefer using the same prescaler for arbitration and data phase
        same_prescaler = list(
            filter(lambda x: x.nom_brp == x.data_brp, possible_solutions)
        )
        if same_prescaler:
            possible_solutions = same_prescaler

        # sort solutions: prefer high tolerance, low prescaler and high sjw
        for key, reverse in (
            (lambda x: x.data_brp, False),
            (lambda x: x.nom_brp, False),
            (lambda x: x.oscillator_tolerance, True),
        ):
            possible_solutions.sort(key=key, reverse=reverse)

        return possible_solutions[0]

    @property
    def nom_bitrate(self) -> int:
        """Nominal (arbitration phase) bitrate."""
        return self["nom_bitrate"]

    @property
    def nom_brp(self) -> int:
        """Prescaler value for the arbitration phase."""
        return int(round(self.f_clock / (self.nom_bitrate * self.nbt)))

    @property
    def nbt(self) -> int:
        """Number of time quanta in a bit of the arbitration phase."""
        return 1 + self.nom_tseg1 + self.nom_tseg2

    @property
    def nom_tseg1(self) -> int:
        """Time segment 1 value of the arbitration phase.

        This is the sum of the propagation time segment and the phase buffer segment 1.
        """
        return self["nom_tseg1"]

    @property
    def nom_tseg2(self) -> int:
        """Time segment 2 value of the arbitration phase. Also known as phase buffer segment 2."""
        return self["nom_tseg2"]

    @property
    def nom_sjw(self) -> int:
        """Synchronization jump width of the arbitration phase.

        The phase buffer segments may be shortened or lengthened by this value.
        """
        return self["nom_sjw"]

    @property
    def nom_sample_point(self) -> float:
        """Sample point of the arbitration phase in percent."""
        return 100.0 * (1 + self.nom_tseg1) / (1 + self.nom_tseg1 + self.nom_tseg2)

    @property
    def data_bitrate(self) -> int:
        """Bitrate of the data phase in bit/s."""
        return self["data_bitrate"]

    @property
    def data_brp(self) -> int:
        """Prescaler value for the data phase."""
        return int(round(self.f_clock / (self.data_bitrate * self.dbt)))

    @property
    def dbt(self) -> int:
        """Number of time quanta in a bit of the data phase."""
        return 1 + self.data_tseg1 + self.data_tseg2

    @property
    def data_tseg1(self) -> int:
        """TSEG1 value of the data phase.

        This is the sum of the propagation time segment and the phase buffer segment 1.
        """
        return self["data_tseg1"]

    @property
    def data_tseg2(self) -> int:
        """TSEG2 value of the data phase. Also known as phase buffer segment 2."""
        return self["data_tseg2"]

    @property
    def data_sjw(self) -> int:
        """Synchronization jump width of the data phase.

        The phase buffer segments may be shortened or lengthened by this value.
        """
        return self["data_sjw"]

    @property
    def data_sample_point(self) -> float:
        """Sample point of the data phase in percent."""
        return 100.0 * (1 + self.data_tseg1) / (1 + self.data_tseg1 + self.data_tseg2)

    @property
    def f_clock(self) -> int:
        """The CAN system clock frequency in Hz.

        Usually the oscillator frequency divided by 2.
        """
        return self["f_clock"]

    @property
    def oscillator_tolerance(self) -> float:
        """Oscillator tolerance in percent."""
        df_clock_list = [
            _oscillator_tolerance_condition_1(nom_sjw=self.nom_sjw, nbt=self.nbt),
            _oscillator_tolerance_condition_2(nbt=self.nbt, nom_tseg2=self.nom_tseg2),
            _oscillator_tolerance_condition_3(data_sjw=self.data_sjw, dbt=self.dbt),
            _oscillator_tolerance_condition_4(
                data_tseg2=self.data_tseg2,
                nbt=self.nbt,
                data_brp=self.data_brp,
                nom_brp=self.nom_brp,
            ),
            _oscillator_tolerance_condition_5(
                data_sjw=self.data_sjw,
                data_brp=self.data_brp,
                nom_brp=self.nom_brp,
                data_tseg2=self.data_tseg2,
                nom_tseg2=self.nom_tseg2,
                nbt=self.nbt,
                dbt=self.dbt,
            ),
        ]
        return max(0.0, min(df_clock_list) * 100)

    def __str__(self) -> str:
        segments = []
        try:
            segments.append(f"NBR: {self.nom_bitrate} bit/s")
        except ValueError:
            pass
        try:
            segments.append(f"NSP: {self.nom_sample_point:.2f}%")
        except ValueError:
            pass
        try:
            segments.append(f"NBRP: {self.nom_brp}")
        except ValueError:
            pass
        try:
            segments.append(f"NTSEG1: {self.nom_tseg1}")
        except ValueError:
            pass
        try:
            segments.append(f"NTSEG2: {self.nom_tseg2}")
        except ValueError:
            pass
        try:
            segments.append(f"NSJW: {self.nom_sjw}")
        except ValueError:
            pass
        try:
            segments.append(f"DBR: {self.data_bitrate} bit/s")
        except ValueError:
            pass
        try:
            segments.append(f"DSP: {self.data_sample_point:.2f}%")
        except ValueError:
            pass
        try:
            segments.append(f"DBRP: {self.data_brp}")
        except ValueError:
            pass
        try:
            segments.append(f"DTSEG1: {self.data_tseg1}")
        except ValueError:
            pass
        try:
            segments.append(f"DTSEG2: {self.data_tseg2}")
        except ValueError:
            pass
        try:
            segments.append(f"DSJW: {self.data_sjw}")
        except ValueError:
            pass
        try:
            segments.append(f"f_clock: {self.f_clock / 1e6:.0f}MHz")
        except ValueError:
            pass
        try:
            segments.append(f"df_clock: {self.oscillator_tolerance:.2f}%")
        except ValueError:
            pass
        return ", ".join(segments)

    def __repr__(self) -> str:
        args = ", ".join(f"{key}={value}" for key, value in self.items())
        return f"can.{self.__class__.__name__}({args})"

    def __getitem__(self, key: str) -> int:
        return cast(int, self._data.__getitem__(key))

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> Iterator[str]:
        return self._data.__iter__()


def _oscillator_tolerance_condition_1(nom_sjw: int, nbt: int) -> float:
    """Arbitration phase - resynchronization"""
    return nom_sjw / (2 * 10 * nbt)


def _oscillator_tolerance_condition_2(nbt: int, nom_tseg2: int) -> float:
    """Arbitration phase - sampling of bit after error flag"""
    return nom_tseg2 / (2 * (13 * nbt - nom_tseg2))


def _oscillator_tolerance_condition_3(data_sjw: int, dbt: int) -> float:
    """Data phase - resynchronization"""
    return data_sjw / (2 * 10 * dbt)


def _oscillator_tolerance_condition_4(
    data_tseg2: int, nbt: int, data_brp: int, nom_brp: int
) -> float:
    """Data phase - sampling of bit after error flag"""
    return data_tseg2 / (2 * ((6 * nbt - data_tseg2) * data_brp / nom_brp + 7 * nbt))


def _oscillator_tolerance_condition_5(
    data_sjw: int,
    data_brp: int,
    nom_brp: int,
    nom_tseg2: int,
    data_tseg2: int,
    nbt: int,
    dbt: int,
) -> float:
    """Data phase - bit rate switch"""
    max_correctable_phase_shift = data_sjw - max(0.0, nom_brp / data_brp - 1)
    time_between_resync = 2 * (
        (2 * nbt - nom_tseg2) * nom_brp / data_brp + data_tseg2 + 4 * dbt
    )
    return max_correctable_phase_shift / time_between_resync
