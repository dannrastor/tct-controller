from core import *
from measurements.async_worker import AsyncWorker


class CalibrateInstrumentsWorker(AsyncWorker):

    description = 'Calibration'

    def action(self):
        core.measurement_state = 0, 2
        if core.oscilloscope is not None:
            core.oscilloscope.calibrate()
        core.measurement_state = 1, 2
        if core.motors is not None:
            core.motors.calibrate()
        core.measurement_state = 1, 2

