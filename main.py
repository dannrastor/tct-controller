from instruments.oscilloscope import Oscilloscope

import itertools
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
    plt.show()

def save_screenshot(path):
    bytes = lecroy.screenshot()
    with open(path, "wb") as binary_file:
        binary_file.write(bytes)


if __name__ == '__main__':
    lecroy = Oscilloscope()
    # save_screenshot("/home/drastorg/Desktop/lecroy_screenshot.png")
    with open('/home/drastorg/Desktop/binary_wf/data.bin', 'wb') as binary_file:
        bytes = lecroy.get_wf_bin(1)
        start = bytes.find(b'WAVEDESC')
        binary_file.write(bytes[start:])
    # draw_wf_plots()


