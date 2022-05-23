# tct-controller

## Dependencies
- `PyQt5` (and a backend!)
- `numpy`
- `pickle`
- `matplotlib`
- `pyvisa`
- `pyvisa-py` backend for `pyvisa`
- `pyserial` (in progress)
- properly configured `linux-gpib` backend for `pyvisa`
- `libximc`

## Modules description

- `core.py` contains `TCTController` class which provides high-level handles for instrumentation. 
A global instance of `TCTController` is created in this module, which should be talked to by GUI with method calls, attributes reference and *maybe* Qt signals (in progress)  
Also contains worker classes which implement routines for running measurements. Worker are to be run asynchronously (`QThread`-based) 
- `gui.py` implements GUI (`PyQt5`) and is a main file. Currently GUI checks instrumentation state by timed queries to the core (may be changed to listening to signals emitted by the core)
- `instruments/oscilloscope.py` provides handle for scope using TCPIP/LXI with `pyvisa-py`
- `instruments/temperature.py` provides handle for Arduino temp readout using `pyserial` (in progress)
- `instruments/motors/motor_controller.py` provides handle for stage controller using `libximc`
- `instruments/motors/pyximc.py` creates global instance of `libximc` and contains python wrappers for C data types used in it
- `instruments/motors/stage_config.py` contains settings loader with predefined settings for Standa 8MT30-50 positioners