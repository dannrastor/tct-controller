import os
import pickle

import numpy
from PyQt5.QtWidgets import *

import core
from core import *
from measurements.async_worker import AsyncWorker


class BiasScanWorker(AsyncWorker):

    description = 'Bias scan'
    has_dialog = True

    def action(self):

        self.result = {}
        self.result['settings'] = self.settings
        vrange = range(*self.settings['vrange'])
        current_steps = 0
        total_steps = len(vrange)
        core.measurement_state = 0, total_steps

        for voltage in vrange:
            if QThread.currentThread().isInterruptionRequested():
                self.save_data()
                return

            if core.hv_source is not None:
                core.hv_source.set_voltage(voltage)

            time.sleep(1)


            for ch in self.settings['channels']:
                if ch not in self.result:
                    self.result[ch] = {}

                if core.oscilloscope is not None:
                    t, v = core.oscilloscope.get_waveform(ch)
                    self.result[ch][voltage] = t, v

            current_steps += 1
            core.measurement_state = current_steps, total_steps
        self.save_data()

    def save_data(self):
        with open(self.settings['path'], 'wb') as f:
            pickle.dump(self.result, f)

    class Dialog(QDialog):
        default_settings = {'vrange': (0, 101, 5),
                            'path': '/home/drastorg/tct/data/out.pickle',
                            'channels': [1, 2],
                            }
        cached_settings = default_settings

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setModal(True)
            self.setWindowTitle('Bias scan configuration')

            self.ret = None

            self.inputs = []

            texts = ['vstart', 'vstop', 'vstep']

            range_box = QGroupBox()
            range_box.setTitle('Voltage range')
            range_box_layout = QHBoxLayout()

            for i in range(3):
                range_box_layout.addWidget(QLabel(texts[i]))
                spinbox = QSpinBox()
                spinbox.setRange(-1100, 1100)
                spinbox.setValue(BiasScanWorker.Dialog.cached_settings['vrange'][i])
                self.inputs.append(spinbox)
                range_box_layout.addWidget(spinbox)
            range_box.setLayout(range_box_layout)

            file_box = QGroupBox()
            file_box.setTitle('Output file')
            file_box_layout = QHBoxLayout()
            self.filename = QLineEdit(BiasScanWorker.Dialog.cached_settings['path'])
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
                if i + 1 in BiasScanWorker.Dialog.cached_settings['channels']:
                    self.channel_ticks[i].setChecked(True)
            channel_box.setLayout(channel_layout)

            layout = QVBoxLayout()
            layout.addWidget(range_box)
            layout.addWidget(channel_box)
            layout.addWidget(file_box)
            layout.addWidget(run_box)
            self.setLayout(layout)

        def __del__(self):
            BiasScanWorker.Dialog.cached_settings = self.extract_settings()

        def choose_file(self):
            self.filename.setText(QFileDialog.getSaveFileName(
                None,
                'Select output file',
                '/home/drastorg/tct/data',
                '', '')[0])

        def extract_settings(self):
            vrange = tuple([item.value() for item in self.inputs])
            output_path = self.filename.text()
            channels = [i + 1 for i, button in enumerate(self.channel_ticks) if button.isChecked()]

            ret = {'vrange': vrange,
                   'path': output_path,
                   'channels': channels,
                   }
            return ret

        def decline(self):
            """
            Executes on 'cancel' click. Just updates cached settings.
            """
            BiasScanWorker.Dialog.cached_settings = self.extract_settings()
            self.reject()

        def finalize(self):
            """
            Executes on 'ok' click. Check correctness of user input. If correct, exit dialog and store data in its self.ret attribute
            """

            vrange = tuple([item.value() for item in self.inputs])
            output_path = self.filename.text()

            if not vrange[2]:
                QMessageBox(QMessageBox.Warning, 'Configuration error', 'Step can\'t be 0!', parent=self).exec()
                return
            if not len(range(*vrange)):
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
            BiasScanWorker.Dialog.cached_settings = self.ret
            self.accept()

