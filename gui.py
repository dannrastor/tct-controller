import os.path

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from core import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import numpy
import sys
import time
from datetime import timedelta
import random


class TctGui(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('TCT')
        self.setGeometry(500, 300, 640, 640)
        self.setWindowIcon(QIcon('./icon.png'))

        self.tabs = QTabWidget()
        self.create_hardware_tab()

        self.tabs.addTab(MeasurementControlWidget(), 'Measurements')
        self.tabs.addTab(QLabel('nothing here'), 'Log')

        self.setCentralWidget(self.tabs)

        self.show()


    def create_hardware_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(ScopeControlWidget())

        layout.addWidget(MotorControlWidget('x'))
        layout.addWidget(MotorControlWidget('y'))
        layout.addWidget(MotorControlWidget('z'))

        tab = QWidget()
        tab.setLayout(layout)

        self.monitoring_tab = tab
        self.tabs.addTab(tab, 'Hardware + Manual control')


class MotorControlWidget(QGroupBox):
    """
    Group of widgets for manual control and status display of a single stage
    """

    def __init__(self, axis):
        super().__init__()

        self.axis = axis
        layout = QHBoxLayout()

        self.name_label = QLabel(f'{self.axis} axis')
        self.pos_label = QLabel()
        self.status_label = QLabel('-')

        self.spinbox = QSpinBox()
        self.spinbox.setRange(-40000, 40000)

        self.move_abs_button = AutoDisablingButton('Move absolute')
        self.move_abs_button.clicked.connect(self.request_abs_move)
        self.move_rel_button = AutoDisablingButton('Move relative')
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
        if core.motors is None:
            self.status_label.setText('Unconnected')
            return
        pos = core.motors.get_position(self.axis)
        self.pos_label.setText(f'{pos} steps')
        if not core.instruments_ready:
            self.status_label.setText('Calibration')
        elif core.motors.is_moving(self.axis):
            self.status_label.setText('Moving')
        else:
            self.status_label.setText('Ready')

    def request_abs_move(self):
        if core.motors is not None and core.instruments_ready:
            core.motors.move_abs(self.axis, self.spinbox.value())

    def request_rel_move(self):
        if core.motors is not None and core.instruments_ready:
            core.motors.move_rel(self.axis, self.spinbox.value())


class ScopeControlWidget(QGroupBox):
    """
    Oscilloscope control widget
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.figure = Figure(figsize=(10, 10))

        self.canvas = FigureCanvasQTAgg(self.figure)

        self.fetch_button = AutoDisablingButton('Fetch waveform')
        self.fetch_button.clicked.connect(self.fetch)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(100)

        layout.addWidget(self.canvas)
        layout.addWidget(self.fetch_button)
        self.setLayout(layout)

    def refresh(self):
        data = None
        if core.instruments_ready:
            data = core.oscilloscope.cached_waveform
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        if data is not None:
            axes.plot(*data)
        self.canvas.draw()

    def fetch(self):
        if core.instruments_ready:
            core.oscilloscope.get_waveform(2)
        self.refresh()


class MeasurementControlWidget(QGroupBox):
    """
    Contents of Measurements tab
    """

    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.run_button = AutoDisablingButton('Configure and run...')
        self.run_button.clicked.connect(self.configure_and_run)
        self.abort_button = AutoDisablingButton('Abort', negative=True)
        self.abort_button.clicked.connect(self.abort)
        self.statusbar = QProgressBar()
        self.table = QTableWidget(6, 2)
        self.fill_table()

        layout.addWidget(self.table, 0, 0, 3, 2)
        layout.addWidget(self.statusbar, 3, 0, 1, 2)
        layout.addWidget(self.run_button, 4, 0, 1, 1)
        layout.addWidget(self.abort_button, 4, 1, 1, 1)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def configure_and_run(self):
        if core.instruments_ready:
            dialog = self.ConfigureDialog(self)
            if dialog.exec():
                print(dialog.ret)
                core.run_measurement(MotorScan(settings=dialog.ret))

    def abort(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Abort measurement')
        dialog.setText('This may lead to a data loss. Abort anyway?')
        dialog.setStandardButtons(QMessageBox.Abort | QMessageBox.Cancel)
        if dialog.exec() == QMessageBox.Abort:
            core.abort_measurement()

    def refresh(self):
        self.statusbar.setMinimum(0)
        self.statusbar.setMaximum(core.measurement_state[1])
        self.statusbar.setValue(core.measurement_state[0])
        self.fill_table()

    def fill_table(self):

        f = lambda x, y, s: self.table.setItem(x, y, QTableWidgetItem(str(s)))

        f(0, 0, 'Measurement status')
        f(1, 0, 'Measurement type')
        f(2, 0, 'Current step')
        f(3, 0, 'Total steps')
        f(4, 0, 'Elapsed time')
        f(5, 0, 'Estimated time')

        if core.is_measurement_running:
            f(0, 1, 'RUNNING')
            f(1, 1, type(core.worker).__name__)  # FIXME
            ms = core.measurement_state
            f(2, 1, ms[0])
            f(3, 1, ms[1])
            elapsed_time = int(time.time()) - core.start_time
            f(4, 1, timedelta(seconds=elapsed_time))
            if ms[0]:
                remaining_time = int(elapsed_time * (ms[1] - ms[0]) / ms[0])
                f(5, 1, timedelta(seconds=remaining_time))
        else:
            f(0, 1, 'IDLE')
            for i in range(1, 6):
                f(i, 1, '')

        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

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

            f = lambda x: tuple([i.value() for i in self.inputs[x:x + 3]])
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


class AutoDisablingButton(QPushButton):
    """
    Button that is disabled when a measurement is running.
    Could be created with negative=True, so it is disabled when a measurement is NOT running.
    Works by listening to core signals.
    """
    def __init__(self, text, negative=False):
        super().__init__(text)
        self.negative = negative
        if negative:
            self.setEnabled(False)
        core.measurement_started.connect(self.on_meas)
        core.measurement_finished.connect(self.off_meas)

    def on_meas(self):
        self.setEnabled(self.negative)

    def off_meas(self):
        self.setEnabled(not self.negative)


if __name__ == '__main__':
    app = QApplication([])
    gui = TctGui()

    # A hack to make the app respond to python's KeyboardInterrupt
    # Interpreter takes over every 500 ms (it can't handle exceptions while on Qt event loop)
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    core.run_measurement(CalibrateInstruments())

    sys.exit(app.exec())
