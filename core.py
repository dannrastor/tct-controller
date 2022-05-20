import pyvisa

from instruments.oscilloscope import Oscilloscope
from instruments.temperature import TemperatureSensor
from instruments.motors.motor_controller import Motors

import pyvisa
import time
import os
import pickle
import numpy
import matplotlib.pyplot as plt


class TCTController():

    def __init__(self):
        self.resource_manager = pyvisa.ResourceManager()

        self.motors = Motors()
        self.motors.calibrate()

        self.oscilloscope = Oscilloscope(self.resource_manager)
        self.oscilloscope.calibrate()

        self.temperature = None
        self.measurement_running = False


if __name__ == '__main__':
    tctc = TCTController()


