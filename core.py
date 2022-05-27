from PyQt5.QtCore import QObject, QThread, pyqtSignal

from instruments.oscilloscope import Oscilloscope
from instruments.motors.motor_controller import Motors

import pyvisa
import time

import logging


class TCTController(QObject):

    measurement_started = pyqtSignal()
    measurement_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.visa_manager = pyvisa.ResourceManager('@py')

        self.oscilloscope = None
        self.motors = None
        self.hv_source = None
        self.temperature = None

        # FIXME replace with signals
        self.start_time = 0
        self.measurement_state = 0, 1
        self.is_measurement_running = False

    def __del__(self):
        self.abort_measurement()

    def connect_instruments(self):
        self.oscilloscope = Oscilloscope(self.visa_manager)
        self.motors = Motors()

    def run_measurement(self, worker):
        """
        Launch measurement thread
        """


        self.measurement_started.emit()
        self.is_measurement_running = True

        self.thread = QThread()
        self.worker = worker

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.finish_measurement)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.start_time = int(time.time())

        logging.info(f'Measurement starting: {self.worker.description}')
        logging.info(f'Settings: {self.worker.settings}')
        self.thread.start()

    def abort_measurement(self):
        if hasattr(self, 'thread') and self.is_measurement_running:
            self.thread.requestInterruption()
            logging.info(f'Abort requested: {self.worker.description}')

    def finish_measurement(self):
        self.measurement_state = 0, 1
        self.is_measurement_running = False
        self.measurement_finished.emit()
        logging.info(f'Measurement finished: {self.worker.description}')


core = TCTController()
