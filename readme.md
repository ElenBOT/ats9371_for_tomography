see video: https://www.youtube.com/watch?v=l_GHQ7Fy5kc&t.
# ATS9371 Driver
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
## import and find card
from ats9371_for_tomography.ats9371 import AlazarTechATS9371
from ats9371_for_tomography.raw_acq_ctrl import RawAcquisitionController
AlazarTechATS9371.find_boards()

## connect to ATS9371
ats_inst = AlazarTechATS9371(name='ATS9371')
acq_ctrl = RawAcquisitionController(
    name='ATS9371_acq', alazar_name='ATS9371'
)
```

Sync settings, see the end of the file for all settings that can be used.
```python
## config setting
ADC_SAMPLING_RATE = 1_000_000_000 # 1GHz
TRIGGER_DELAY_SAMPLES = 8 * 17 # mutiple of 8
with ats_inst.syncing():
    #### clock setting
    ## option1: internal clock with sampling rate setting
    # ats_inst.clock_source("INTERNAL_CLOCK")
    # ats_inst.sample_rate(ADC_SAMPLING_RATE)
    ## option2: external clock, sampling rate is the same as clock
    ats_inst.sample_rate("EXTERNAL_CLOCK")
    ats_inst.clock_source("FAST_EXTERNAL_CLOCK")
    ## option3: 10MHz external clock with sampling rate setting
    # ats_inst.clock_source("EXTERNAL_CLOCK_10MHz_REF")
    # ats_inst.external_sample_rate(ADC_SAMPLING_RATE)

    #### trigger setting
    ats_inst.trigger_operation('TRIG_ENGINE_OP_J')
    ats_inst.trigger_engine1("TRIG_ENGINE_J")
    ats_inst.trigger_source1("EXTERNAL")
    # ats_inst.external_trigger_range()
    ats_inst.trigger_slope1("TRIG_SLOPE_POSITIVE")
    ats_inst.trigger_level1(150) # 0~255
    ats_inst.trigger_delay(0)
    ats_inst.trigger_source2("DISABLE")

## acquisition setting
NUMBER_OF_RECORDS = 5000 # trace per acquisition
NUMBER_OF_SAMPLES = 128*25 # samples per trace, multiple of 128
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
