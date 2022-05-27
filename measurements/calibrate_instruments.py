from measurements.async_worker import AsyncWorker
from core import *


class CalibrateInstrumentsWorker(AsyncWorker):

    def action(self):
        core.measurement_state = 0, 2
        core.oscilloscope.calibrate()
        core.measurement_state = 1, 2
        core.motors.calibrate()
        core.measurement_state = 1, 2

