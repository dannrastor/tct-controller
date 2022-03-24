from instruments.oscilloscope import Oscilloscope

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

def draw_bin_plots():
    for ch in range(1, 4):
        st = lecroy.get_wf_bin(ch)
        nb, t, v = lecroy.parse_binary_wf(st)
        if ch == 3:
            v /= 10
        plt.plot(t/(1e-9), v)
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



if __name__ == '__main__':
    lecroy = Oscilloscope()
    # save_screenshot("/home/drastorg/Desktop/lecroy_screenshot.png")
    # with open('/home/drastorg/Desktop/binary_wf/data.bin', 'wb') as binary_file:
    #     bytes = lecroy.get_wf_bin(1)
    #     start = bytes.find(b'WAVEDESC')
    #     binary_file.write(bytes[start:])
    # draw_bin_plots()
    idiot_series()


