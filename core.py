from PyQt5.QtCore import QObject, QThread, pyqtSignal

from instruments.oscilloscope import Oscilloscope
from instruments.temperature import TemperatureSensor
from instruments.motors.motor_controller import Motors

import pyvisa
import time

import pickle
import numpy


class TCTController(QObject):

    measurement_started = pyqtSignal()
    measurement_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.visa_manager = pyvisa.ResourceManager()

        self.oscilloscope = Oscilloscope(self.visa_manager)
        self.motors = Motors()
        self.hv_source = None
        self.temperature = None

        # FIXME replace with signals
        self.start_time = 0
        self.measurement_state = 0, 1
        self.is_measurement_running = False
        self.instruments_ready = False

    def calibrate(self):
        self.instruments_ready = False
        self.oscilloscope.calibrate()
        self.motors.calibrate()
        self.instruments_ready = True

    def __del__(self):
        self.abort_measurement()

    def run_measurement(self, worker):
        """
        Launch measurement thread
        """
        print('Measurement starting')

        self.measurement_started.emit()
        self.is_measurement_running = True

        self.thread = QThread()

        # FiXME: allow for use of different workers
        self.worker = worker

        self.worker.moveToThread(self.thread)
        self.worker.progress_tick.connect(self.update_progress)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.finish_measurement)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.start_time = int(time.time())
        self.thread.start()

    def abort_measurement(self):
        if hasattr(self, 'thread') and self.is_measurement_running:
            self.finish_measurement()
            self.thread.requestInterruption()

    def finish_measurement(self):
        self.measurement_state = 0, 1
        self.is_measurement_running = False
        self.measurement_finished.emit()

    def update_progress(self, a, b):
        self.measurement_state = a, b


core = TCTController()


class AsyncRoutine(QObject):
    finished = pyqtSignal()
    progress_tick = pyqtSignal(int, int)

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings

    def run(self):
        self.action()
        self.finished.emit()

    def action(self):
        # Long task here
        # You'd better emit progress_tick signals meanwhile
        pass


class CalibrateInstruments(AsyncRoutine):

    def action(self):
        core.calibrate()


class MotorScan(AsyncRoutine):

    def action(self):

        xrange, yrange, zrange = self.settings['xrange'], self.settings['yrange'], self.settings['zrange']
        current_steps = 0
        total_steps = len(range(*xrange)) * len(range(*yrange)) * len(range(*zrange))
        self.progress_tick.emit(0, total_steps)

        for x in range(*xrange):
            for y in range(*yrange):
                for z in range(*zrange):

                    if QThread.currentThread().isInterruptionRequested():
                        print('MotorScan: aborting')
                        self.finished.emit()
                        return

                    core.motors.move_abs('x', x)
                    core.motors.move_abs('y', y)
                    core.motors.move_abs('z', z)

                    # Delay between move command and state check is crucial, the latter fails otherwise
                    # Controller response time is several ms

                    time.sleep(0.05)
                    while core.motors.is_moving('x') or core.motors.is_moving('y') or core.motors.is_moving('z'):
                        time.sleep(0.05)

                    time.sleep(1)

                    core.oscilloscope.get_waveform(2)

                    current_steps += 1
                    self.progress_tick.emit(current_steps, total_steps)
        self.finished.emit()
