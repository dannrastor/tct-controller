from measurements.async_worker import AsyncWorker
from core import *
from PyQt5.QtWidgets import *
import os


class MotorScanWorker(AsyncWorker):

    description = 'Position scan'

    def action(self):

        xrange, yrange, zrange = self.settings['xrange'], self.settings['yrange'], self.settings['zrange']
        current_steps = 0
        total_steps = len(range(*xrange)) * len(range(*yrange)) * len(range(*zrange))
        core.measurement_state = 0, total_steps

        for x in range(*xrange):
            for y in range(*yrange):
                for z in range(*zrange):

                    if QThread.currentThread().isInterruptionRequested():
                        return

                    core.motors.move_abs('x', x)
                    core.motors.move_abs('y', y)
                    core.motors.move_abs('z', z)

                    # Delay between move command and state check is crucial, the latter fails otherwise
                    # Controller response time is several ms

                    time.sleep(0.05)
                    while core.motors.is_moving('x') or core.motors.is_moving('y') or core.motors.is_moving('z'):
                        time.sleep(0.05)

                    time.sleep(1)

                    core.oscilloscope.get_waveform(2)

                    current_steps += 1
                    core.measurement_state = current_steps, total_steps


class MotorScanConfigureDialog(QDialog):

    def __init__(self, parent=None):
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