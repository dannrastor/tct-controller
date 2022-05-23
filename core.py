from PyQt5.QtCore import QObject, QThread, pyqtSignal, QMutex

from instruments.oscilloscope import Oscilloscope
from instruments.temperature import TemperatureSensor
from instruments.motors.motor_controller import Motors

import pyvisa
import time

import pickle
import numpy


class TCTController(QObject):

    def __init__(self):
        super().__init__()

        self.resource_manager = pyvisa.ResourceManager()

        self.oscilloscope = Oscilloscope(self.resource_manager)
        self.oscilloscope.calibrate()

        self.motors = Motors()
        self.motors.calibrate()

        self.temperature = None

        # FIXME replace with signals
        self.measurement_state = 0, 0
        self.measurement_running = False

        # fixme
        self.motors_running = QMutex()

    def motor_scan(self, settings):
        """
        Launch measurement thread
        """
        self.thread = QThread()
        self.worker = MotorScan(settings)
        self.worker.moveToThread(self.thread)
        self.worker.progress_tick.connect(self.update_progress)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_progress(self, a, b):
        self.measurement_state = a, b


core = TCTController()


class MotorScan(QObject):
    finished = pyqtSignal()
    progress_tick = pyqtSignal(int, int)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):

        for x in range(*self.settings['xrange']):
            for y in range(*self.settings['yrange']):
                for z in range(*self.settings['zrange']):

                    core.motors_running.lock()
                    core.motors.move_abs('x', x)
                    core.motors.move_abs('y', y)
                    core.motors.move_abs('z', z)

                    # Delay between move command and state check is crucial, the latter fails otherwise
                    # Controller response time is several ms

                    time.sleep(0.05)
                    while core.motors.is_moving('x') or core.motors.is_moving('y') or core.motors.is_moving('z'):
                        time.sleep(0.05)
                    core.motors_running.unlock()

                    time.sleep(1)

                    core.oscilloscope.get_waveform(2)
                    self.progress_tick.emit(x, y)
        self.finished.emit()
