import os
import pickle

import numpy
from PyQt5.QtWidgets import *

import core
from core import *
from measurements.async_worker import AsyncWorker


class FocusCheckWorker(AsyncWorker):
    description = 'Focus check (single shot)'

    def action(self):
        pass



class FocusCheckConfigureDialog(QDialog):
    default_settings = {'x1': 16800,
                        'y1': 8125,
                        'x2': 17400,
                        'y2': 8125,
                        'z': 34000,
                        'channel': 2,
                        }
    cached_settings = default_settings

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle('Focus check configuration')

        self.ret = None

        self.inputs = []
        texts = ['x1', 'y1', 'x2', 'y2', 'z']
        range_box_layout = QHBoxLayout()
        for i, t in enumerate(texts):
            inp = QSpinBox()
            inp.setRange(0, 40000)
            inp.setValue(self.cached_settings[t])
            self.inputs.append(inp);
            range_box_layout.addWidget(QLabel(t))
            range_box_layout.addWidget(inp)

        range_box = QGroupBox()
        range_box.setTitle('Coordinate params')
        range_box.setLayout(range_box_layout)



        run_box = QWidget()
        run_layout = QHBoxLayout()
        self.ok_button = QPushButton('Start scan')
        self.ok_button.clicked.connect(self.finalize)
        run_layout.addWidget(self.ok_button)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.decline)
        run_layout.addWidget(self.cancel_button)
        run_box.setLayout(run_layout)

        channel_box = QGroupBox()
        channel_box.setTitle('Channels')
        channel_layout = QHBoxLayout()
        self.channel_ticks = []
        for i in range(3):
            self.channel_ticks.append(QRadioButton(f'CH{i + 1}'))
            channel_layout.addWidget(self.channel_ticks[i])
            if i + 1 == FocusCheckConfigureDialog.cached_settings['channel']:
                self.channel_ticks[i].setChecked(True)
        channel_box.setLayout(channel_layout)

        layout = QVBoxLayout()
        layout.addWidget(range_box)
        layout.addWidget(channel_box)
        layout.addWidget(run_box)
        self.setLayout(layout)

    def __del__(self):
        FocusCheckConfigureDialog.cached_settings = self.extract_settings()


    def extract_settings(self):

        channels = [i + 1 for i, button in enumerate(self.channel_ticks) if button.isChecked()]

        ret = {'x1': self.inputs[0].value(),
               'y1': self.inputs[1].value(),
               'x2': self.inputs[2].value(),
               'y2': self.inputs[3].value(),
               'z': self.inputs[4].value(),
               'channel': channels[0],
               }
        return ret

    def decline(self):
        """
        Executes on 'cancel' click. Just updates cached settings.
        """
        FocusCheckConfigureDialog.cached_settings = self.extract_settings()
        self.reject()

    def finalize(self):
        """
        Executes on 'ok' click. Check correctness of user input. If correct, exit dialog and store data in its self.ret attribute
        """


        self.ret = self.extract_settings()
        FocusCheckConfigureDialog.cached_settings = self.ret
        self.accept()
