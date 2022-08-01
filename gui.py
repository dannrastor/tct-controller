import sys

from PyQt5.QtGui import QIcon

from utils.gui_logger import *
from utils.widgets import *
from measurements.calibrate_instruments import CalibrateInstrumentsWorker



class TctGui(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('TCT')
        self.setGeometry(500, 300, 1000, 800)
        self.setWindowIcon(QIcon('./icon.png'))

        self.tabs = QTabWidget()
        self.create_hardware_tab()
        self.tabs.addTab(MeasurementControlWidget(), 'Measurements')
        self.create_log_tab()
        self.setCentralWidget(self.tabs)

        self.show()

    def create_hardware_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(ScopeControlWidget())

        layout.addWidget(MotorControlWidget('x'))
        layout.addWidget(MotorControlWidget('y'))
        layout.addWidget(MotorControlWidget('z'))
        layout.addWidget(HVWidget())
        layout.addWidget(TemperatureWidget())

        tab = QWidget()
        tab.setLayout(layout)

        self.monitoring_tab = tab
        self.tabs.addTab(tab, 'Hardware + Manual control')

    def create_log_tab(self):
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)

        gui_logger.changed.connect(self.log_view.appendPlainText)
        self.tabs.addTab(self.log_view, 'Log')





if __name__ == '__main__':
    app = QApplication([])
    gui = TctGui()

    # A hack to make the app respond to python's KeyboardInterrupt
    # Interpreter takes over every 500 ms (it can't handle exceptions while on Qt event loop)
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    core.connect_instruments()
    core.run_measurement(CalibrateInstrumentsWorker())

    sys.exit(app.exec())
