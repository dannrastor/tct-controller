import os.path

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

        self.tabs.addTab(MeasurementGUI(), 'Measurements')
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
    """
    Group of widgets for manual control and status display of a single stage
    """

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
        self.timer.start(10)

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
    """
    Oscilloscope control widget
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.figure = Figure(figsize=(10, 10))

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
        self.refresh()


class MeasurementGUI(QGroupBox):
    """
    Contents of Measurements tab
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.run_button = QPushButton('Run measurement')
        self.run_button.clicked.connect(self.configure_and_run)
        self.statusbar = QLabel('Run status')
        layout.addWidget(self.run_button)
        layout.addWidget(self.statusbar)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10)

    def configure_and_run(self):
        dialog = self.ConfigureDialog(self)
        if dialog.exec():
            print(dialog.ret)
            core.motor_scan(dialog.ret)

    def refresh(self):
        self.statusbar.setText(str(core.measurement_state))

    class ConfigureDialog(QDialog):

        def __init__(self, parent):
            super().__init__(parent)
            self.setModal(True)
            self.setWindowTitle('Motor scan configuration')

            self.ret = None

            self.inputs = []
            layout = QGridLayout()

            for i in range(9):
                text = ''
                if i // 3 == 0: text = 'x'
                if i // 3 == 1: text = 'y'
                if i // 3 == 2: text = 'z'
                if i % 3 == 0: text += 'start'
                if i % 3 == 1: text += 'stop'
                if i % 3 == 2: text += 'step'
                layout.addWidget(QLabel(text), i // 3, (i % 3) * 2)
                spinbox = QSpinBox()
                spinbox.setRange(0, 40000)
                if (i % 3 == 2):
                    spinbox.setRange(-40000, 40000)
                    spinbox.setValue(1)
                self.inputs.append(spinbox)
                layout.addWidget(spinbox, i // 3, (i % 3) * 2 + 1)

            self.filename = QLineEdit('/path/to/output/file.pickle')
            layout.addWidget(self.filename, 3, 0, 1, 5)
            self.file_button = QPushButton('Select...')
            self.file_button.clicked.connect(self.choose_file)
            layout.addWidget(self.file_button, 3, 5)

            self.ok_button = QPushButton('Start scan')
            self.ok_button.clicked.connect(self.finalize)
            layout.addWidget(self.ok_button, 4, 0, 1, 3)
            self.cancel_button = QPushButton('Cancel')
            self.cancel_button.clicked.connect(self.reject)
            layout.addWidget(self.cancel_button, 4, 3, 1, 3)

            self.setLayout(layout)

        def choose_file(self):
            path = QFileDialog.getSaveFileName()[0]
            self.filename.setText(path)

        def finalize(self):
            """
            Check correctness of user input. If correct, exit dialog and store data in its self.ret attribute
            """

            f = lambda x: tuple([i.value() for i in self.inputs[x:x+3]])
            xrange, yrange, zrange = f(0), f(3), f(6)
            output_path = self.filename.text()

            mb = QMessageBox(self)
            mb.setWindowTitle('Configuration error')
            if not (xrange[2] and yrange[2] and zrange[2]):
                mb.setText('Step can\'t be 0!')
                mb.exec()
                return
            if not (len(range(*xrange)) and len(range(*yrange)) and len(range(*zrange))):
                mb.setText('There must be at least 1 step on every direction')
                mb.exec()
                return
            if not os.path.exists(os.path.dirname(output_path)):
                mb.setText('Invalid path')
                mb.exec()
                return

            self.ret = {'xrange': xrange,
                        'yrange': yrange,
                        'zrange': zrange,
                        'path': output_path}
            self.accept()


if __name__ == '__main__':
    app = QApplication([])
    gui = TctGui()

    sys.exit(app.exec())
