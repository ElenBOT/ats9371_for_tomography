I use QCoDeS to perform fast acquisition of raw data from the 
AlazarTech ATS9371 card, optimized for use case of tomography.
This code is directly copied and moidfied from modules in QCoDeS.

# Setting up the enviroment
Use conda to create an enviroment then install qcodes. The "qcodes" below is the name for the env, you may name it by yours.
```
conda create -n qcodes python=3.9
conda activate qcodes
pip install qcodes
```

# Connect and setting
Import and connect.
```python
from ATS9371_for_tomography.ats9371 import AlazarTechATS9371
from ATS9371_for_tomography.raw_acq_ctrl import RawAcquisitionController
# connect to ATS9371
ats_inst = AlazarTechATS9371(name='ATS9371')
acq_ctrl = RawAcquisitionController(
    name='ATS9371_acq', alazar_name='ATS9371'
)
```

Sync settings, see the end of the file for all settings that can be used.
```python
# config setting
SAMPLING_RATE = 1_000_000_000 # 1GHz
with ats_inst.syncing():
    ats_inst.clock_source("INTERNAL_CLOCK")
    ats_inst.sample_rate(SAMPLING_RATE)
    ats_inst.trigger_operation('TRIG_ENGINE_OP_J')
    ats_inst.trigger_engine1("TRIG_ENGINE_J")
    ats_inst.trigger_source1("EXTERNAL")
    ats_inst.trigger_slope1("TRIG_SLOPE_POSITIVE")
    ats_inst.trigger_level1(160)
    ats_inst.trigger_delay(1400) # samples
    ats_inst.trigger_source2("DISABLE")
# acquisition setting
NUMBER_OF_RECORDS = 8192 # trace per acquisition, max 84MB
NUMBER_OF_SAMPLES = 3200 # samples per trace
acq_ctrl.update_acquisitionkwargs(
    samples_per_record = NUMBER_OF_SAMPLES,
    records_per_buffer = NUMBER_OF_RECORDS,
    buffers_per_acquisition = 1,
    allocated_buffers = 1,
)
```

# Aquire raw data
* `do_acquisition`: Aquire into buffer of `acq_ctrl`.
* `numpy_get_alldata_from_buffer_in_volt`: Read from buffer.
* `numba_get_alldata_from_buffer_in_volt`: Read from buffer.

numpy version and numba version do the same thing, but numba one might be faster, depend on computer used.
```python
# aquire and stored data into chaA, chaB.
acq_ctrl.do_acquisition()
chaA, chaB = acq_ctrl.numpy_get_alldata_from_buffer_in_volt()
chaA, chaB = acq_ctrl.numba_get_alldata_from_buffer_in_volt()
```
(Note: For aquire without trigger, you may use Alazar Tech DSO to aquire a trace, then run the code below. Might be an TODO task to make it work without using DSO, but I skip it for now.) 

# Available settings

Below are settings that can be appiled as `ats_inst."setting"`: 
`clock_source`,
`external_sample_rate`,
`sample_rate`,
`clock_edge`,
`decimation`,
`coupling1`,
`channel_range1`,
`impedance1`,
`coupling2`,
`channel_range2`,
`impedance2`,
`trigger_operation`,
`trigger_engine1`,
`trigger_source1`,
`trigger_slope1`,
`trigger_level1`,
`trigger_engine2`,
`trigger_source2`,
`trigger_slope2`,
`trigger_level2`,
`external_trigger_coupling`,
`external_trigger_range`,
`trigger_delay`,
`timeout_ticks`,
`aux_io_mode`,
`aux_io_param`,
`mode`,
`samples_per_record`,
`records_per_buffer`,
`buffers_per_acquisition`,
`channel_selection`,
`transfer_offset`,
`external_startcapture`,
`enable_record_headers`,
`alloc_buffers`,
`fifo_only_streaming`,
`interleave_samples`,
`get_processed_data`,
`allocated_buffers`,
`buffer_timeout`,
`trigger_holdoff`.
