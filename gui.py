from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from core import *
from measurements.calibrate_instruments import CalibrateInstrumentsWorker
from measurements.motor_scan import MotorScanWorker, MotorScanConfigureDialog

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import sys
import time
from datetime import timedelta


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

        if core.is_measurement_running:
            if type(core.worker).__name__ == 'CalibrateInstruments':
                self.status_label.setText('Calibration')
                return
        if core.motors.is_moving(self.axis):
            self.status_label.setText('Moving')
        else:
            self.status_label.setText('Ready')

    def request_abs_move(self):
        if core.motors is not None:
            core.motors.move_abs(self.axis, self.spinbox.value())

    def request_rel_move(self):
        if core.motors is not None:
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
        if not core.is_measurement_running:
            data = core.oscilloscope.cached_waveform
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        if data is not None:
            axes.plot(*data)
        self.canvas.draw()

    def fetch(self):
        core.oscilloscope.get_waveform(2)
        self.refresh()


class MeasurementControlWidget(QGroupBox):
    """
    Contents of Measurements tab
    """

    def __init__(self):
        super().__init__()

        self.run_button = AutoDisablingButton('Configure and run...')
        self.run_button.clicked.connect(self.configure_and_run)

        self.abort_button = AutoDisablingButton('Abort', negative=True)
        self.abort_button.clicked.connect(self.abort)

        self.statusbar = QProgressBar()

        self.table = QTableWidget(6, 2)
        self.fill_table()

        self.combobox = QComboBox()
        self.combobox.addItems(['Calibrate instruments', 'Spatial scan'])

        layout = QGridLayout()
        layout.addWidget(self.table, 0, 0, 3, 3)
        layout.addWidget(self.statusbar, 3, 0, 1, 3)
        layout.addWidget(self.combobox, 4, 0, 1, 1)
        layout.addWidget(self.run_button, 4, 1, 1, 1)
        layout.addWidget(self.abort_button, 4, 2, 1, 1)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def configure_and_run(self):
        s = self.combobox.currentIndex()
        if s == 0:
            core.run_measurement(CalibrateInstrumentsWorker())
        if s == 1:
            dialog = MotorScanConfigureDialog(parent=self)
            if dialog.exec():
                core.run_measurement(MotorScanWorker(dialog.ret))


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

    core.run_measurement(CalibrateInstrumentsWorker())

    sys.exit(app.exec())
