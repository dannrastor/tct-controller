from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from core import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import numpy
import sys
import random


class TctGui(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('TCT')
        self.setGeometry(500, 300, 1000, 800)
        self.setWindowIcon(QIcon('./icon.png'))

        self.tabs = QTabWidget()
        self.create_monitoring_tab()
        self.tabs.addTab(QLabel('nothing here'), 'Measurements')
        self.tabs.addTab(QLabel('nothing here'), 'Log')

        self.setCentralWidget(self.tabs)

        self.show()

    def create_monitoring_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(WaveformPlot())

        layout.addWidget(MotorStatus('x'))
        layout.addWidget(MotorStatus('y'))
        layout.addWidget(MotorStatus('z'))

        tab = QWidget()
        tab.setLayout(layout)

        self.monitoring_tab = tab
        self.tabs.addTab(tab, 'Monitoring')


class MotorStatus(QGroupBox):
    def __init__(self, axis):
        super().__init__()

        self.axis = axis
        layout = QHBoxLayout()

        self.name_label = QLabel(f'{self.axis} axis')
        self.pos_label = QLabel()
        self.status_label = QLabel('FIXME')

        self.spinbox = QSpinBox()
        self.spinbox.setRange(-40000, 40000)

        self.move_abs_button = QPushButton('Move absolute')
        self.move_abs_button.clicked.connect(self.request_abs_move)
        self.move_rel_button = QPushButton('Move relative')
        self.move_rel_button.clicked.connect(self.request_rel_move)

        layout.addWidget(self.name_label)
        layout.addWidget(self.pos_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.spinbox)
        layout.addWidget(self.move_abs_button)
        layout.addWidget(self.move_rel_button)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(100)

    def refresh(self):
        pos = core.motors.get_position(self.axis)
        self.pos_label.setText(f'{pos} steps')
        if core.motors.is_moving(self.axis):
            self.status_label.setText('Moving')
        else:
            self.status_label.setText('Ready')

    def request_abs_move(self):
        core.motors.move_abs(self.axis, self.spinbox.value())

    def request_rel_move(self):
        core.motors.move_rel(self.axis, self.spinbox.value())


class WaveformPlot(QGroupBox):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.figure = Figure(figsize=(10,10))

        self.canvas = FigureCanvasQTAgg(self.figure)

        self.fetch_button = QPushButton('Fetch waveform')
        self.fetch_button.clicked.connect(self.fetch)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(100)

        layout.addWidget(self.canvas)
        layout.addWidget(self.fetch_button)
        self.setLayout(layout)

    def refresh(self):
        data = core.oscilloscope.cached_waveform
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        if data is not None:
            axes.plot(*data)
        self.canvas.draw()

    def fetch(self):
        core.oscilloscope.get_waveform(2)



if __name__ == '__main__':
    core = TCTController()

    app = QApplication([])
    gui = TctGui()

    sys.exit(app.exec())
