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

        self.motors = None
        self.oscilloscope = None
        self.temperature = None

        self.measurement_running = False

        self.connect_oscilloscope()

    def connect_oscilloscope(self):
        try:
            self.oscilloscope = Oscilloscope(self.resource_manager)
        except Exception:
            pass

        self.oscilloscope.calibrate()





def idiot_series():
    path = '/home/drastorg/Desktop/laser_pulse/filter/'
    while True:
        dac_value = input('Input DAC value: ')
        fp = path + dac_value + '.pickle'
        data1 = lecroy.parse_raw_waveform(lecroy.get_raw_waveform(1))
        data3 = lecroy.parse_raw_waveform(lecroy.get_raw_waveform(3))
        oh = (data1, data3)
        with open(fp, 'wb') as f:
            pickle.dump(oh, f)


def scan_motors():
    path = '/home/drastorg/tct/atlas_chip_050522'

    result = {}
    first = True

    motors.move_abs('y', 5800, 0)

    for z in range(22000, 23500, 200):
        result[z] = {}
        for x in range(17500, 17900, 10):

            motors.move_abs('x', x, 0)
            motors.move_abs('z', z, 0)
            if first:
                time.sleep(2)
                first = False
            motors.print_positions('steps')

            time.sleep(1)
            data = lecroy.parse_raw_waveform(lecroy.get_raw_waveform(2))

            result[z][x] = data

    with open(os.path.join(path, 'd9.pickle'), 'wb') as f:
        pickle.dump(result, f)


if __name__ == '__main__':
    lecroy = Oscilloscope()
    lecroy.calibrate()

    motors = Motors()

    motors.calibrate()

    scan_motors()
