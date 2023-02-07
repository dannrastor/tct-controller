# A guide to external measurement scripts with the TCT setup

The intended way to use the setup for automated measurements with external devices (e.g. Caribou) 
is to write external control scripts.

To control the setup from such a script, one should import `tct_remote_client.py` and create an instance of TCTClient.
Constructor takes address and port of the lab PC as arguments, these are `fhltctscan.desy.de:8888` or `131.169.43.35:8888`.
A `ConnectionError` is raised from constructor if connection fails.
Method calls of TCTClient will control actual components (motors and HV implemented atm) of the setup.
See `tct_remote_client.py` for details.

The process is as follows:
1. Launch the tct-controller (`gui.py`) at the lab PC and wait for instruments to calibrate.
2. If necessary, adjust motors and HV manually (this is locked when remote controlling).
3. Go to "Measurements" tab, select "External control", click "Configure and run". The lab PC will now listen to a client connection.
4. Run a measurement script on a user PC. If working correctly, stuff is displayed in the "Log" tab.

NB: the "External control" routine only listens to incoming connection upon launch. 
To run next measurement, one needs to stop it 
(either by clicking "Abort" in the gui or by calling `TCTClient.stop()` on a client side) and start again.

An example of an external Python script:
```python
from tct_remote_client import TCTClient
import time

tct = TCTClient('fhltctscan.desy.de', 8888)

for z in range(...)
    tct.move(23.3, 9.9, z)
    time.sleep(1.0)
    # Request whatever measurement from some other tools


tct.stop()
```