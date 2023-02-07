import datetime
import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from core import *
from measurements.calibrate_instruments import CalibrateInstrumentsWorker
from measurements.motor_scan import MotorScanWorker, MotorScanConfigureDialog
from measurements.bias_scan import BiasScanWorker, BiasScanConfigureDialog
from measurements.laser_stability import LaserStabilityWorker
from measurements.external_control import ExternalControlWorker


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

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(-50, 50)
        self.spinbox.setDecimals(4)

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
        self.pos_label.setText(f'{pos:.4f} mm')

        if core.is_measurement_running:
            if core.worker.description == 'Calibration':
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
    channel_to_color = {1: 'orange', 2: 'magenta', 3: 'tab:blue'}

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        button_area = QWidget()
        buttons_layout = QHBoxLayout()

        self.figure = Figure(figsize=(10, 10))

        self.canvas = FigureCanvasQTAgg(self.figure)

        self.fetch_button = AutoDisablingButton('Fetch waveform')
        self.fetch_button.clicked.connect(self.fetch)

        self.screenshot_button = QPushButton('Save screenshot')
        self.screenshot_button.clicked.connect(self.screenshot)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(100)

        layout.addWidget(self.canvas)
        buttons_layout.addWidget(self.fetch_button)
        buttons_layout.addWidget(self.screenshot_button)
        button_area.setLayout(buttons_layout)
        layout.addWidget(button_area)
        self.setLayout(layout)

    def refresh(self):
        """
        Plot cached waveforms stored in oscilloscope object
        """

        if core.oscilloscope is None:
            return

        data = core.oscilloscope.cached_waveform
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        for key, value in data.items():
            x, y = value
            axes.plot(x / 1e-9, y / 1e-3, color=self.channel_to_color[key])
        axes.set_xlabel('t, ns')
        axes.set_ylabel('signal, mV')
        self.canvas.draw()

    def fetch(self):
        """
        Force acquisition with scope, which will update cached wfs
        """

        if core.oscilloscope is None:
            return

        for i in [1, 2]:
            core.oscilloscope.get_waveform(i)
        self.refresh()

    def screenshot(self):
        if core.oscilloscope is None:
            return

        datetime_str = datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S')
        filename = 'screenshot_' + datetime_str + '.png'
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../screenshots', filename))
        core.oscilloscope.save_screenshot(path)
        logging.info('Saved screenshot: ' + path)


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
        self.combobox.addItems(['Calibrate instruments', 'Position scan', 'Bias scan', 'Laser stability', 'External control'])

        layout = QGridLayout()
        layout.addWidget(self.table, 0, 0, 3, 3)
        layout.addWidget(self.statusbar, 3, 0, 1, 3)
        layout.addWidget(self.combobox, 4, 0, 1, 1)
        layout.addWidget(self.run_button, 4, 1, 1, 1)
        layout.addWidget(self.abort_button, 4, 2, 1, 1)
        self.setLayout(layout)

        # a workaround to mute popup after initial calibration FIXME
        self.first = True
        core.measurement_finished.connect(self.finished_popup)

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
        if s == 2:
            dialog = BiasScanConfigureDialog(parent=self)
            if dialog.exec():
                core.run_measurement(BiasScanWorker(dialog.ret))
        if s == 3:
            core.run_measurement(LaserStabilityWorker())
        if s == 4:
            core.run_measurement(ExternalControlWorker())

    def abort(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Abort measurement')
        dialog.setText('Sure?')
        dialog.setStandardButtons(QMessageBox.Abort | QMessageBox.Cancel)
        if dialog.exec() == QMessageBox.Abort:
            core.abort_measurement()

    def finished_popup(self):
        if not self.first:
            QMessageBox(QMessageBox.Information, '', 'Measurement finished!', parent=self).exec()
        self.first = False

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
            f(1, 1, core.worker.description)
            ms = core.measurement_state
            f(2, 1, ms[0])
            f(3, 1, ms[1])
            elapsed_time = int(time.time()) - core.start_time
            f(4, 1, datetime.timedelta(seconds=elapsed_time))
            if ms[0]:
                remaining_time = int(elapsed_time * (ms[1] - ms[0]) / ms[0])
                f(5, 1, datetime.timedelta(seconds=remaining_time))
        else:
            f(0, 1, 'IDLE')
            for i in range(1, 6):
                f(i, 1, '')

        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


class TemperatureWidget(QGroupBox):
    def __init__(self):
        super().__init__()

        self.ch1_label = QLabel('-')
        self.ch2_label = QLabel('-')

        layout = QHBoxLayout()
        layout.addWidget(QLabel('Temperatures'))
        layout.addWidget(self.ch1_label)
        layout.addWidget(self.ch2_label)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def refresh(self):
        if core.temperature is not None:
            t1 = core.temperature.get_value(1)
            t2 = core.temperature.get_value(2)
            if t1:
                self.ch1_label.setText(f'Ch1:  {float(t1):.1f}{chr(176)}C')
            if t2:
                self.ch2_label.setText(f'Ch2:  {float(t2):.1f}{chr(176)}C')


class HVWidget(QGroupBox):
    def __init__(self):
        super().__init__()

        self.on_button = QPushButton('On/Off')
        self.on_button.clicked.connect(self.toggle)
        self.iv_label = QLabel()
        self.state_label = QLabel('-')
        self.setv_button = AutoDisablingButton('Set voltage')
        self.setv_button.clicked.connect(self.setv)
        self.v_spinbox = QDoubleSpinBox()
        self.v_spinbox.setRange(-1100, 1100)

        layout = QHBoxLayout()

        layout.addWidget(QLabel('HV source'))
        layout.addWidget(self.iv_label)
        layout.addWidget(self.state_label)
        layout.addWidget(self.v_spinbox)
        layout.addWidget(self.setv_button)
        layout.addWidget(self.on_button)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.meas)
        self.timer.start(1000)

    def toggle(self):
        if core.hv_source is not None:
            if core.hv_source.is_on():
                core.hv_source.off()
            else:
                core.hv_source.on()

    def setv(self):
        if core.hv_source is not None:
            core.hv_source.set_voltage(self.v_spinbox.value())

    def meas(self):
        if core.hv_source is not None:
            v, i = core.hv_source.get_current()
            self.state_label.setText('ON' if core.hv_source.is_on() else 'OFF')
            self.iv_label.setText(f'{v:.2f} V; {i / 1e-6:.3f} uA')
        else:
            self.state_label.setText('Unconnected')


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
