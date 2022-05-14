from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import numpy
import sys
import random

class TctGui(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('TCT')
        self.setGeometry(500, 300, 800, 600)
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
        self.pos = 0
        self.status = 'unavailable'
        
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
        self.timer.start(2000)
 
        
    def refresh(self):
        self.pos += random.randint(0, 10)
        self.pos_label.setText(f'{self.pos} steps')
        self.status = 'stopped (FIXME)'
        self.status_label.setText(self.status)
        
    def request_abs_move(self):
        self.pos = self.spinbox.value()
        self.status = 'moving'
        
    def request_rel_move(self):
        self.pos += self.spinbox.value()
        self.status = 'moving'
    
    
class WaveformPlot(FigureCanvasQTAgg):
    
    def __init__(self):
        fig = Figure(figsize=(10, 10))
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.axes.plot(range(10), [random.random() for i in range(10)])
      
        
    

if __name__ == '__main__':

    app = QApplication([])
    gui = TctGui()

    sys.exit(app.exec())
