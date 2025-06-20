"""ATS9371 control object.

This is direclty modified from `AlazarTechATS9371.py`.

I only modify three things:
1. modify the modle string, so Alazar API can be detected.
2. modify the sampling rate upper bound for ATS9371 (the mapping is the same).
3. Delete the bandwith limit setting, for ATS9371 don't have it.

"""
from typing import TYPE_CHECKING, Any

import numpy as np
from packaging import version

from qcodes import validators
from qcodes.instrument_drivers.AlazarTech.ATS import AlazarTechATS
from qcodes.instrument_drivers.AlazarTech.utils import TraceParameter

if TYPE_CHECKING:
    from qcodes.parameters import Parameter


class AlazarTechATS9371(AlazarTechATS):
    """
    This class is the driver for the ATS9371 board.

    Note that this board is very similar to ATS9360. Refer to
    ATS SDK for details.

    Note that channels of this board have 12-bit resolution
    (see `IDN()['bits_per_sample']`) which means that the
    raw data that is returned by the card should be converted to
    uint16 type with a bit shift by 4 bits. Refer to ATS SDK
    for more infromation.
    """
    samples_divisor = 128
    _trigger_holdoff_min_fw_version = '30.04'

    def __init__(self, name: str,
                 dll_path: str = 'C:\\WINDOWS\\System32\\ATSApi.dll',
                 **kwargs: Any):
        super().__init__(name, dll_path=dll_path, **kwargs)

        # add parameters

        # ----- Parameters for the configuration of the board -----
        self.clock_source: TraceParameter = self.add_parameter(
            name="clock_source",
            parameter_class=TraceParameter,
            label="Clock Source",
            unit=None,
            initial_value="INTERNAL_CLOCK",
            val_mapping={
                "INTERNAL_CLOCK": 1,
                "FAST_EXTERNAL_CLOCK": 2,
                "EXTERNAL_CLOCK_10MHz_REF": 7,
            },
        )
        """Parameter clock_source"""
        self.external_sample_rate: TraceParameter = self.add_parameter(
            name="external_sample_rate",
            parameter_class=TraceParameter,
            label="External Sample Rate",
            unit="S/s",
            vals=validators.MultiType(
                validators.Ints(300000000, 2000000000), validators.Enum("UNDEFINED")
            ),
            initial_value="UNDEFINED",
        )
        """Parameter external_sample_rate"""
        self.sample_rate: TraceParameter = self.add_parameter(
            name="sample_rate",
            parameter_class=TraceParameter,
            label="Internal Sample Rate",
            unit="S/s",
            initial_value="UNDEFINED",
            val_mapping={
                1_000: 1,
                2_000: 2,
                5_000: 4,
                10_000: 8,
                20_000: 10,
                50_000: 12,
                100_000: 14,
                200_000: 16,
                500_000: 18,
                1_000_000: 20,
                2_000_000: 24,
                5_000_000: 26,
                10_000_000: 28,
                20_000_000: 30,
                25_000_000: 33,
                50_000_000: 34,
                100_000_000: 36,
                125_000_000: 37,
                160_000_000: 38,
                180_000_000: 39,
                200_000_000: 40,
                250_000_000: 43,
                500_000_000: 48,
                800_000_000: 50,
                1_000_000_000: 53,
                "EXTERNAL_CLOCK": 64,
                "UNDEFINED": "UNDEFINED",
            },
        )
        """Parameter sample_rate"""
        self.clock_edge: TraceParameter = self.add_parameter(
            name="clock_edge",
            parameter_class=TraceParameter,
            label="Clock Edge",
            unit=None,
            initial_value="CLOCK_EDGE_RISING",
            val_mapping={"CLOCK_EDGE_RISING": 0, "CLOCK_EDGE_FALLING": 1},
        )
        """Parameter clock_edge"""
        self.decimation: TraceParameter = self.add_parameter(
            name="decimation",
            parameter_class=TraceParameter,
            label="Decimation",
            unit=None,
            initial_value=1,
            vals=validators.Ints(0, 100000),
        )
        """Parameter decimation"""

        for i in range(1, self.channels+1):
            self.add_parameter(name=f'coupling{i}',
                               parameter_class=TraceParameter,
                               label=f'Coupling channel {i}',
                               unit=None,
                               initial_value='DC',
                               val_mapping={'AC': 1, 'DC': 2})
            self.add_parameter(name=f'channel_range{i}',
                               parameter_class=TraceParameter,
                               label=f'Range channel {i}',
                               unit='V',
                               initial_value=0.4,
                               val_mapping={0.4: 7})
            self.add_parameter(name=f'impedance{i}',
                               parameter_class=TraceParameter,
                               label=f'Impedance channel {i}',
                               unit='Ohm',
                               initial_value=50,
                               val_mapping={50: 2})
            

        self.trigger_operation: TraceParameter = self.add_parameter(
            name="trigger_operation",
            parameter_class=TraceParameter,
            label="Trigger Operation",
            unit=None,
            initial_value="TRIG_ENGINE_OP_J",
            val_mapping={
                "TRIG_ENGINE_OP_J": 0,
                "TRIG_ENGINE_OP_K": 1,
                "TRIG_ENGINE_OP_J_OR_K": 2,
                "TRIG_ENGINE_OP_J_AND_K": 3,
                "TRIG_ENGINE_OP_J_XOR_K": 4,
                "TRIG_ENGINE_OP_J_AND_NOT_K": 5,
                "TRIG_ENGINE_OP_NOT_J_AND_K": 6,
            },
        )
        """Parameter trigger_operation"""
        n_trigger_engines = 2

        for i in range(1, n_trigger_engines+1):
            self.add_parameter(name=f'trigger_engine{i}',
                               parameter_class=TraceParameter,
                               label=f'Trigger Engine {i}',
                               unit=None,
                               initial_value='TRIG_ENGINE_' + ('J' if i == 1 else 'K'),
                               val_mapping={'TRIG_ENGINE_J': 0,
                                            'TRIG_ENGINE_K': 1})
            self.add_parameter(name=f'trigger_source{i}',
                               parameter_class=TraceParameter,
                               label=f'Trigger Source {i}',
                               unit=None,
                               initial_value='EXTERNAL',
                               val_mapping={'CHANNEL_A': 0,
                                            'CHANNEL_B': 1,
                                            'EXTERNAL': 2,
                                            'DISABLE': 3})
            self.add_parameter(name=f'trigger_slope{i}',
                               parameter_class=TraceParameter,
                               label=f'Trigger Slope {i}',
                               unit=None,
                               initial_value='TRIG_SLOPE_POSITIVE',
                               val_mapping={'TRIG_SLOPE_POSITIVE': 1,
                                            'TRIG_SLOPE_NEGATIVE': 2})
            self.add_parameter(name=f'trigger_level{i}',
                               parameter_class=TraceParameter,
                               label=f'Trigger Level {i}',
                               unit=None,
                               initial_value=140,
                               vals=validators.Ints(0, 255))

        self.external_trigger_coupling: TraceParameter = self.add_parameter(
            name="external_trigger_coupling",
            parameter_class=TraceParameter,
            label="External Trigger Coupling",
            unit=None,
            initial_value="DC",
            val_mapping={"AC": 1, "DC": 2},
        )
        """Parameter external_trigger_coupling"""
        self.external_trigger_range: TraceParameter = self.add_parameter(
            name="external_trigger_range",
            parameter_class=TraceParameter,
            label="External Trigger Range",
            unit=None,
            initial_value="ETR_2V5",
            val_mapping={"ETR_TTL": 2, "ETR_2V5": 3},
        )
        """Parameter external_trigger_range"""
        self.trigger_delay: TraceParameter = self.add_parameter(
            name="trigger_delay",
            parameter_class=TraceParameter,
            label="Trigger Delay",
            unit="Sample clock cycles",
            initial_value=0,
            vals=validators.Multiples(divisor=8, min_value=0),
        )
        """Parameter trigger_delay"""
        # See Table 3 - Trigger Delay Alignment
        # TODO: this is either 8 or 16 dependent on the  number of channels in use

        # NOTE: The board will wait for a for this amount of time for a
        # trigger event.  If a trigger event does not arrive, then the
        # board will automatically trigger. Set the trigger timeout value
        # to 0 to force the board to wait forever for a trigger event.
        #
        # IMPORTANT: The trigger timeout value should be set to zero after
        # appropriate trigger parameters have been determined, otherwise
        # the board may trigger if the timeout interval expires before a
        # hardware trigger event arrives.
        self.timeout_ticks: TraceParameter = self.add_parameter(
            name="timeout_ticks",
            parameter_class=TraceParameter,
            label="Timeout Ticks",
            unit="10 us",
            initial_value=0,
            vals=validators.Ints(min_value=0),
        )
        """Parameter timeout_ticks"""

        self.aux_io_mode: TraceParameter = self.add_parameter(
            name="aux_io_mode",
            parameter_class=TraceParameter,
            label="AUX I/O Mode",
            unit=None,
            initial_value="AUX_IN_AUXILIARY",
            val_mapping={
                "AUX_OUT_TRIGGER": 0,
                "AUX_IN_TRIGGER_ENABLE": 1,
                "AUX_IN_AUXILIARY": 13,
            },
        )
        """Parameter aux_io_mode"""
        self.aux_io_param: TraceParameter = self.add_parameter(
            name="aux_io_param",
            parameter_class=TraceParameter,
            label="AUX I/O Param",
            unit=None,
            initial_value="NONE",
            val_mapping={"NONE": 0, "TRIG_SLOPE_POSITIVE": 1, "TRIG_SLOPE_NEGATIVE": 2},
        )
        """Parameter aux_io_param"""

        # ----- Parameters for the acquire function -----
        self.mode: Parameter = self.add_parameter(
            name="mode",
            label="Acquisition mode",
            unit=None,
            initial_value="NPT",
            set_cmd=None,
            val_mapping={"NPT": 0x200, "TS": 0x400},
        )
        """Parameter mode"""
        self.samples_per_record: Parameter = self.add_parameter(
            name="samples_per_record",
            label="Samples per Record",
            unit=None,
            initial_value=1024,
            set_cmd=None,
            vals=validators.Multiples(divisor=self.samples_divisor, min_value=256),
        )
        """Parameter samples_per_record"""
        self.records_per_buffer: Parameter = self.add_parameter(
            name="records_per_buffer",
            label="Records per Buffer",
            unit=None,
            initial_value=10,
            set_cmd=None,
            vals=validators.Ints(min_value=0),
        )
        """Parameter records_per_buffer"""
        self.buffers_per_acquisition: Parameter = self.add_parameter(
            name="buffers_per_acquisition",
            label="Buffers per Acquisition",
            unit=None,
            set_cmd=None,
            initial_value=10,
            vals=validators.Ints(min_value=0),
        )
        """Parameter buffers_per_acquisition"""
        self.channel_selection: Parameter = self.add_parameter(
            name="channel_selection",
            label="Channel Selection",
            unit=None,
            set_cmd=None,
            initial_value="AB",
            val_mapping={"A": 1, "B": 2, "AB": 3},
        )
        """Parameter channel_selection"""
        self.transfer_offset: Parameter = self.add_parameter(
            name="transfer_offset",
            label="Transfer Offset",
            unit="Samples",
            set_cmd=None,
            initial_value=0,
            vals=validators.Ints(min_value=0),
        )
        """Parameter transfer_offset"""
        self.external_startcapture: Parameter = self.add_parameter(
            name="external_startcapture",
            label="External Startcapture",
            unit=None,
            set_cmd=None,
            initial_value="ENABLED",
            val_mapping={"DISABLED": 0x0, "ENABLED": 0x1},
        )
        """Parameter external_startcapture"""
        self.enable_record_headers: Parameter = self.add_parameter(
            name="enable_record_headers",
            label="Enable Record Headers",
            unit=None,
            set_cmd=None,
            initial_value="DISABLED",
            val_mapping={"DISABLED": 0x0, "ENABLED": 0x8},
        )
        """Parameter enable_record_headers"""
        self.alloc_buffers: Parameter = self.add_parameter(
            name="alloc_buffers",
            label="Alloc Buffers",
            unit=None,
            set_cmd=None,
            initial_value="DISABLED",
            val_mapping={"DISABLED": 0x0, "ENABLED": 0x20},
        )
        """Parameter alloc_buffers"""
        self.fifo_only_streaming: Parameter = self.add_parameter(
            name="fifo_only_streaming",
            label="Fifo Only Streaming",
            unit=None,
            set_cmd=None,
            initial_value="DISABLED",
            val_mapping={"DISABLED": 0x0, "ENABLED": 0x800},
        )
        """Parameter fifo_only_streaming"""
        self.interleave_samples: Parameter = self.add_parameter(
            name="interleave_samples",
            label="Interleave Samples",
            unit=None,
            set_cmd=None,
            initial_value="DISABLED",
            val_mapping={"DISABLED": 0x0, "ENABLED": 0x1000},
        )
        """Parameter interleave_samples"""
        self.get_processed_data: Parameter = self.add_parameter(
            name="get_processed_data",
            label="Get Processed Data",
            unit=None,
            set_cmd=None,
            initial_value="DISABLED",
            val_mapping={"DISABLED": 0x0, "ENABLED": 0x2000},
        )
        """Parameter get_processed_data"""
        self.allocated_buffers: Parameter = self.add_parameter(
            name="allocated_buffers",
            label="Allocated Buffers",
            unit=None,
            set_cmd=None,
            initial_value=4,
            vals=validators.Ints(min_value=0),
        )
        """Parameter allocated_buffers"""
        self.buffer_timeout: Parameter = self.add_parameter(
            name="buffer_timeout",
            label="Buffer Timeout",
            unit="ms",
            set_cmd=None,
            initial_value=1000,
            vals=validators.Ints(min_value=0),
        )
        """Parameter buffer_timeout"""

        self.trigger_holdoff: Parameter = self.add_parameter(
            name="trigger_holdoff",
            label="Trigger Holdoff",
            docstring=f"If enabled Alazar will "
            f"ignore any additional triggers "
            f"while capturing a record. If disabled "
            f"a trigger signal during a capture "
            f"will result in corrupt data. "
            f"Support for this requires at least "
            f"firmware version "
            f"{self._trigger_holdoff_min_fw_version}",
            vals=validators.Bool(),
            get_cmd=self._get_trigger_holdoff,
            set_cmd=self._set_trigger_holdoff,
        )
        """
        If enabled Alazar will ignore any additional triggers
        while capturing a record.
        """

        model = self.get_idn()["model"]
        if model != "ATS9371":
            raise Exception(
                f"The Alazar board kind is not 'ATS9371',"
                f" found '{model!s}' instead."
            )

    def _get_trigger_holdoff(self) -> bool:
        fwversion = self.get_idn()["firmware"]
        if not isinstance(fwversion, str) or version.parse(fwversion) < version.parse(
            self._trigger_holdoff_min_fw_version
        ):
            return False

        # we want to check if the 26h bit (zero indexed) is high or not
        output = np.uint32(self._read_register(58))
        # the two first two chars in the bit string is the sign and a 'b'
        # remove those to only get the bit pattern
        bitmask = bin(output)[2:]
        # all prefixed zeros are ignored in the bit conversion so the
        # bit mask may be shorter than what we expect. in that case
        # the bit we care about is zero so we return False
        if len(bitmask) < 27:
            return False

        return bool(bin(output)[-27])

    def _set_trigger_holdoff(self, value: bool) -> None:
        fwversion = self.get_idn()["firmware"]
        if not isinstance(fwversion, str) or version.parse(fwversion) < version.parse(
            self._trigger_holdoff_min_fw_version
        ):
            raise RuntimeError(
                f"Alazar 9371 requires at least firmware "
                f"version {self._trigger_holdoff_min_fw_version}"
                f" for trigger holdoff support. "
                f"You have version {fwversion}"
            )
        current_value = self._read_register(58)

        if value is True:
            # to enable trigger hold off we want to flip the
            # 26th bit to 1. We do that by making a bitwise or
            # with a number that has a 1 on the 26th place and zero
            # otherwise. We use numpy.unit32 instead of python numbers
            # to have unsigned ints of the right size
            enable_mask = np.uint32(1 << 26)
            new_value = current_value | enable_mask
        else:
            # to disable trigger hold off we want to flip the
            # 26th bit to 0. We do that by making a bitwise and
            # with a number that has a 0 on the 26th place and 1
            # otherwise
            disable_mask = ~np.uint32(1 << 26)
            new_value = current_value & disable_mask
        self._write_register(58, int(new_value))


class AlazarTech_ATS9371(AlazarTechATS9371):
    """
    Alias for backwards compatibility. Will eventually be deprecated and removed
    """

    pass
