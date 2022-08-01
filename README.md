# tct-controller

## Dependencies
- `PyQt5` (and a backend!)
- `numpy`
- `pickle`
- `matplotlib`
- `pyvisa`
- `pyvisa-py` backend for `pyvisa`
- `pyserial` (in progress)
- properly configured `linux-gpib` backend for `pyvisa` (deprecated, will switch to RS232 interface)
- `libximc`

## Modules description

- `core.py` provides `TCTController` class which owns handles for different instruments. This class is also responsible for measurements running and management. 
A global instance of `TCTController` is created in this module, which should be talked to by the GUI with method calls, attributes reference and Qt signals.
- `gui.py` implements GUI (`PyQt5`) and is a main file. Currently GUI checks instrumentation state by timed queries to the core (some part of it will be changed to listening to signals emitted by the core)
- `instruments.oscilloscope.py` provides handle for scope using TCPIP/LXI with `pyvisa-py`
- `instruments.temperature.py` provides handle for Arduino temp readout using `pyserial`
- `instruments.motors.motor_controller.py` provides handle for stage controller using `libximc`
- `instruments.motors.pyximc.py` creates a global instance of `libximc` and contains python wrappers for C data types used in it
- `instruments.motors.stage_config.py` contains a settings loader with predefined settings for Standa 8MT30-50 positioners
- `measurements.async_worker.py` contains a base class for measurement workers
- `measurements.calibrate_instruments.py` contains a corresponding worker
- `measurements.motor_scan.py` a corresponding worker and related gui elements (config dialog)
- `utils.widgets.py` contains UI elements and corresponding logic
- `utils.gui_logger.py` contains some setup for built-in `logging`