from instruments.oscilloscope import Oscilloscope
from instruments.temperature import TemperatureSensor
from instruments.motors.motor_controller import Motors

import time
import os
import itertools
import pickle
import numpy as np
import matplotlib.pyplot as plt


def parse_wf_string(st):
    """Convert INSPECT query output to numpy array"""
    st = st.split('\r\n')
    st = st[1:-1]
    st = [item.split() for item in st]
    st = list(itertools.chain.from_iterable(st))
    return np.array([float(i) for i in st])


def draw_wf_plots():
    """Run INSPECT queries for channels and plot the data"""
    for ch in range(1, 4):
        st = lecroy.get_wf_string(ch)
        data = parse_wf_string(st)
        plt.plot(np.arange(data.shape[0]), data)
    plt.grid()
    plt.show()


def save_screenshot(path):
    bytes = lecroy.screenshot()
    with open(path, "wb") as binary_file:
        binary_file.write(bytes)


def idiot_series():
    path = '/home/drastorg/Desktop/laser_pulse/filter/'
    while True:
        dac_value = input('Input DAC value: ')
        fp = path + dac_value + '.pickle'
        data1 = lecroy.parse_binary_wf(lecroy.get_wf_bin(1))
        data3 = lecroy.parse_binary_wf(lecroy.get_wf_bin(3))
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
            data = lecroy.parse_binary_wf(lecroy.get_wf_bin(2))

            result[z][x] = data

    with open(os.path.join(path, 'd9.pickle'), 'wb') as f:
        pickle.dump(result, f)


if __name__ == '__main__':
    lecroy = Oscilloscope()
    lecroy.calibrate()

    motors = Motors()

    motors.calibrate()

    scan_motors()
