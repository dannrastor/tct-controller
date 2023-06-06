import os
import pickle

import numpy
from PyQt5.QtWidgets import *

import core
from core import *
from measurements.async_worker import AsyncWorker





class MotorScanWorker(AsyncWorker):

    description = 'Position scan'
    has_dialog = True

    def action(self):

        self.result = {}
        self.result['settings'] = self.settings
        self.result['currents'] = {}
        xrange = numpy.arange(*self.settings['xrange'])
        yrange = numpy.arange(*self.settings['yrange'])
        zrange = numpy.arange(*self.settings['zrange'])

        current_steps = 0
        total_steps = len(xrange) * len(yrange) * len(zrange)
        core.measurement_state = 0, total_steps

        for x in xrange:
            for y in yrange:
                for z in zrange:

                    if QThread.currentThread().isInterruptionRequested():
                        self.save_data()
                        return

                    if core.motors is not None:
                        core.motors.move_abs('x', x)
                        core.motors.move_abs('y', y)
                        core.motors.move_abs('z', z)

                        # Delay between move command and state check is crucial, the latter fails otherwise
                        # Controller response time is several ms

                        time.sleep(0.05)

                        while core.motors.is_moving('x') or core.motors.is_moving('y') or core.motors.is_moving('z'):
                            time.sleep(0.05)

                        time.sleep(0.5)

                    # self.result[(x, y, z)] = {}
                    for ch in self.settings['channels']:
                        if ch not in self.result:
                            self.result[ch] = {}

                        if core.oscilloscope is not None:
                            t, v = core.oscilloscope.get_waveform(ch)
                            if self.settings['save_integral']:
                                self.result[ch][(x, y, z)] = numpy.sum(v)
                            else:
                                self.result[ch][(x, y, z)] = t, v

                        if core.hv_source is not None:
                            with core.hv_source.lock:
                                i = core.hv_source.get_current()[1]
                            self.result['currents'][(x, y, z)] = i

                    current_steps += 1
                    core.measurement_state = current_steps, total_steps
        self.save_data()

    def save_data(self):
        with open(self.settings['path'], 'wb') as f:
            pickle.dump(self.result, f)

    class Dialog(QDialog):
        default_settings = {'xrange': (0, 40.1, 10),
                            'yrange': (0, 40.1, 10),
                            'zrange': (0, 1, 1),
                            'path': '/home/drastorg/tct/data/out.pickle',
                            'channels': [1, 2],
                            'save_integral': True}
        cached_settings = default_settings

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setModal(True)
            self.setWindowTitle('Motor scan configuration')

            self.ret = None

            self.inputs = []

            texts = ['xstart', 'xstop', 'xstep', 'ystart', 'ystop', 'ystep', 'zstart', 'zstop', 'zstep']
            values = ['xrange'] * 3 + ['yrange'] * 3 + ['zrange'] * 3
            values = list(zip(values, [0, 1, 2] * 3))

            range_box = QGroupBox()
            range_box.setTitle('Coordinate ranges')
            range_box_layout = QGridLayout()
            for i in range(9):
                range_box_layout.addWidget(QLabel(texts[i]), i // 3, (i % 3) * 2)
                spinbox = QDoubleSpinBox()
                spinbox.setDecimals(4)
                spinbox.setRange(0, 50)
                if (i % 3 == 2):
                    spinbox.setRange(-50, 50)
                spinbox.setValue(MotorScanWorker.Dialog.cached_settings[values[i][0]][values[i][1]])

                self.inputs.append(spinbox)
                range_box_layout.addWidget(spinbox, i // 3, (i % 3) * 2 + 1)
            range_box.setLayout(range_box_layout)

            file_box = QGroupBox()
            file_box.setTitle('Output file')
            file_box_layout = QHBoxLayout()
            self.filename = QLineEdit(MotorScanWorker.Dialog.cached_settings['path'])
            file_box_layout.addWidget(self.filename)
            self.file_button = QPushButton('Select...')
            self.file_button.clicked.connect(self.choose_file)
            file_box_layout.addWidget(self.file_button)
            file_box.setLayout(file_box_layout)

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
                self.channel_ticks.append(QCheckBox(f'CH{i + 1}'))
                channel_layout.addWidget(self.channel_ticks[i])
                if i + 1 in MotorScanWorker.Dialog.cached_settings['channels']:
                    self.channel_ticks[i].setChecked(True)
            channel_box.setLayout(channel_layout)

            datatype_box = QGroupBox()
            datatype_box.setTitle('Data to store')
            datatype_box_layout = QHBoxLayout()
            self.save_integral_button = QRadioButton('Only integral')
            self.save_all_button = QRadioButton('Full waveforms')
            if MotorScanWorker.Dialog.cached_settings['save_integral']:
                self.save_integral_button.setChecked(True)
            else:
                self.save_all_button.setChecked(True)
            datatype_box_layout.addWidget(self.save_all_button)
            datatype_box_layout.addWidget(self.save_integral_button)

            datatype_box.setLayout(datatype_box_layout)

            layout = QVBoxLayout()
            layout.addWidget(range_box)
            layout.addWidget(channel_box)
            layout.addWidget(datatype_box)
            layout.addWidget(file_box)
            layout.addWidget(run_box)
            self.setLayout(layout)

        def __del__(self):
            MotorScanWorker.Dialog.cached_settings = self.extract_settings()

        def choose_file(self):
            self.filename.setText(QFileDialog.getSaveFileName(
                None,
                'Select output file',
                '/home/drastorg/tct/data',
                '', '')[0])

        def extract_settings(self):
            f = lambda x: tuple([i.value() for i in self.inputs[x:x + 3]])
            xrange, yrange, zrange = f(0), f(3), f(6)
            output_path = self.filename.text()
            save_integral = self.save_integral_button.isChecked()
            channels = [i + 1 for i, button in enumerate(self.channel_ticks) if button.isChecked()]

            ret = {'xrange': xrange,
                   'yrange': yrange,
                   'zrange': zrange,
                   'path': output_path,
                   'channels': channels,
                   'save_integral': save_integral}
            return ret

        def decline(self):
            """
            Executes on 'cancel' click. Just updates cached settings.
            """
            MotorScanWorker.Dialog.cached_settings = self.extract_settings()
            self.reject()

        def finalize(self):
            """
            Executes on 'ok' click. Check correctness of user input. If correct, exit dialog and store data in its self.ret attribute
            """

            f = lambda x: tuple([i.value() for i in self.inputs[x:x + 3]])
            xrange, yrange, zrange = f(0), f(3), f(6)
            output_path = self.filename.text()

            if not (xrange[2] and yrange[2] and zrange[2]):
                QMessageBox(QMessageBox.Warning, 'Configuration error', 'Step can\'t be 0!', parent=self).exec()
                return
            if not (len(numpy.arange(*xrange)) and len(numpy.arange(*yrange)) and len(numpy.arange(*zrange))):
                QMessageBox(QMessageBox.Warning, 'Configuration error', 'Must be at least one step!',
                            parent=self).exec()
                return
            if not os.path.exists(os.path.dirname(output_path)):
                QMessageBox(QMessageBox.Warning, 'Configuration error', 'Invalid path!', parent=self).exec()
                return
            if not any([i.isChecked() for i in self.channel_ticks]):
                QMessageBox(QMessageBox.Warning, 'Configuration error', 'Select at least one channel!',
                            parent=self).exec()
                return

            self.ret = self.extract_settings()
            MotorScanWorker.Dialog.cached_settings = self.ret
            self.accept()



