"""Object for aquiring non-averaged raw data from Alazar card.

This is directly modified from `DemodulationAcquisitionController.py`

I modify the following things:
1. Delete demodulation utility like LO sine-cosine array.
2. Delete averaging post-processing codes.
3. Write two versions of get data method to read raw datas efficiently.
-- 1. numpy_get_alldata_from_buffer_in_volt: use numpy to do the conversion.
-- 2. numba_get_alldata_from_buffer_in_volt: use numba, a JIT compiler, to do faster conversion.
"""

import math
from typing import TYPE_CHECKING, Any, Optional
import numba
import numpy as np


from qcodes.instrument_drivers.AlazarTech import AcquisitionController

if TYPE_CHECKING:
    from qcodes.parameters import Parameter


@numba.njit(parallel=True)
def process_buffer(buffer, cha_A, cha_B, n_records, n_samples):
    """The parallel computing to convert raw data to volt and also split into two channels.

    For our use case, this method is tested to be faster then numpy method by around 250% ~ 400%.
    The raw data in the buffer is stored as [A, B, A, B, A, B, ...] patten,
    for raw data to voltage conversion, see docsting of old function `signal_to_volt`.
    """
    for r in numba.prange(n_records):
        for s in range(n_samples):
            i = (r * n_samples + s) * 2
            cha_A[r, s] = (buffer[i]     - 32760) / 81900.0 # -int for not converting datatype
            cha_B[r, s] = (buffer[i + 1] - 32760) / 81900.0 # /float for not converting datatype

def signal_to_volt(signal):
    """
    After testing, the read value is 16 per resolution. And this card can read
    -400mV ~ 400mV with 12 bit resolution. -400mV is expressed as 0. So we have conversion
    volt = (signal - 32760) / 16 * 0.8 / (2**12-1)
    then I expand it to be more efficient.
    """
    return (signal - 32760) / 81900.0


# DFT AcquisitionController
class RawAcquisitionController(AcquisitionController[float]):
    """
    
    Args:
        name: name for this acquisition_conroller as an instrument

        alazar_name: the name of the alazar instrument such that this controller
            can communicate with the Alazar

        **kwargs: kwargs are forwarded to the Instrument base class

    """
    def __init__(
            self,
            name: str,
            alazar_name: str,
            **kwargs: Any):
        self.acquisitionkwargs: dict[str, Any] = {}
        self.samples_per_record = 0
        self.records_per_buffer = 0
        self.buffers_per_acquisition = 0
        self.number_of_channels = 2
        self.buffer: Optional[np.ndarray] = None
        # make a call to the parent class and by extension, create the parameter
        # structure of this class
        super().__init__(name, alazar_name, **kwargs)
        self.acquisition: Parameter = self.add_parameter(
            "acquisition", get_cmd=self.do_acquisition
        )
        """Parameter acquisition"""

    def update_acquisitionkwargs(self, **kwargs: Any) -> None:
        """
        This method must be used to update the kwargs used for the acquisition
        with the alazar_driver.acquire
        :param kwargs:
        :return:
        """
        self.acquisitionkwargs.update(**kwargs)

    def do_acquisition(self) -> float:
        """
        this method performs an acquisition, which is the get_cmd for the
        acquisiion parameter of this instrument
        :return:
        """
        self._get_alazar().acquire(acquisition_controller=self,
                                   **self.acquisitionkwargs)

    def numpy_get_alldata_from_buffer_in_volt(self, copy=True) -> tuple:
        """
        Get channel A and channel B data as 2d np array.
        Return as cha_A, cha_B tuple for chaA[n, :] is n-th trace.

        If copy is Fasle, the returned cha_A and cha_B are views of the internal buffers,
        modifying them will modify the internal buffers, and it will be modified in the next get data.
        So don't use copy=False unless you know what you are doing, however, it is around 15% faster.
        """
        reshaped = self.buffer.reshape(self.records_per_buffer, -1, 2)
        cha_A_raw = reshaped[:, :, 0] # view, no allocation
        cha_B_raw = reshaped[:, :, 1] # view, no allocation

        # volt = (raw - 32760) / 16 * 0.8 / (2**12-1)
        # In-place computation, no allocation
        np.subtract(cha_A_raw, 32760, out=self.cha_A_buffer)
        self.cha_A_buffer /= 81900.0
        np.subtract(cha_B_raw, 32760, out=self.cha_B_buffer)
        self.cha_B_buffer /= 81900.0

        if copy:
            return self.cha_A_buffer.copy(), self.cha_B_buffer.copy()
        else:
            return self.cha_A_buffer, self.cha_B_buffer

    def numba_get_alldata_from_buffer_in_volt(self, copy=True):
        """Get channel A and channel B data as cha_A, cha_B tuple for chaA[n, :] is n-th trace.

        This method is more efficient than `old_get_alldata_from_buffer_in_volt` by use
        numba to do parallel computing.

        If copy is Fasle, the returned cha_A and cha_B are views of the internal buffers,
        modifying them will modify the internal buffers, and it will be modified in the next get data.
        So don't use copy=False unless you know what you are doing, however, it is around 15% faster.
        """
        process_buffer(
            self.buffer, # raw data buffer
            self.cha_A_buffer,
            self.cha_B_buffer,
            self.records_per_buffer,
            self.samples_per_record,
        )
        if copy:
            return self.cha_A_buffer.copy(), self.cha_B_buffer.copy()
        else:
            return self.cha_A_buffer, self.cha_B_buffer

    # devlog: there are not faster then directly using raw data buffer
    # def accumulate_buffer_to_avg_buffer(self) -> None:
    #     """
    #     This method accumulates the current buffer to the average buffer.
    #     This is used to accumulate the data for averaging purposes efficiently.
    #     """
    #     np.add(self.avg_buffer, self.buffer, out=self.avg_buffer)
    # def get_avg_from_avgbuffer_in_volt(self, n_shots=1) -> np.ndarray:
    #     """
    #     compute the average from the average buffer in volt.
    #     returns cha_A_avg, cha_B_avg tuple.
    #     """
    #     reshaped = self.buffer.reshape(self.records_per_buffer, -1, 2)
    #     cha_A_raw_avg = np.sum(reshaped[:, :, 0], axis=0) / n_shots
    #     cha_B_raw_avg = np.sum(reshaped[:, :, 1], axis=0) / n_shots

    #     # volt = (raw - 32760) / 16 * 0.8 / (2**12-1)
    #     cha_A_avg = (cha_A_raw_avg - 32760) / 81900.0
    #     cha_B_avg = (cha_B_raw_avg - 32760) / 81900.0
    #     return cha_A_avg, cha_B_avg

    def pre_start_capture(self) -> None:
        """
        See AcquisitionController
        """
        alazar = self._get_alazar()
        self.samples_per_record = alazar.samples_per_record.get()
        self.records_per_buffer = alazar.records_per_buffer.get()
        self.buffers_per_acquisition = alazar.buffers_per_acquisition.get()
        self.buffer = np.zeros(self.samples_per_record *
                               self.records_per_buffer *
                               self.number_of_channels)
        # self.avg_buffer = np.zeros(self.samples_per_record *
        #                            self.records_per_buffer *
        #                            self.number_of_channels)
        self.cha_A_buffer = np.zeros((self.records_per_buffer, self.samples_per_record))
        self.cha_B_buffer = np.zeros((self.records_per_buffer, self.samples_per_record))


    def pre_acquire(self) -> None:
        """
        See AcquisitionController
        :return:
        """
        # this could be used to start an Arbitrary Waveform Generator, etc...
        # using this method ensures that the contents are executed AFTER the
        # Alazar card starts listening for a trigger pulse
        pass

    def handle_buffer(
        self, buffer: np.ndarray, buffer_number: Optional[int] = None
    ) -> None:
        """
        See AcquisitionController
        :return:
        """
        assert self.buffer is not None
        self.buffer += buffer

    def post_acquire(self) -> float:
        """
        See AcquisitionController
        :return:
        """
        pass


class Raw_AcquisitionController(RawAcquisitionController):
    """
    Alias for backwards compatibility. Will eventually be deprecated and removed
    """

    pass
