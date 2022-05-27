import logging
from PyQt5.QtCore import QObject, pyqtSignal


class GuiLogger(logging.Handler, QObject):
    changed = pyqtSignal(str)

    def __init__(self): 
        logging.Handler.__init__(self)
        QObject.__init__(self)
        formatter = logging.Formatter('%(asctime)s -- %(filename)s -- %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        self.changed.emit(msg)


gui_logger = GuiLogger()
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(gui_logger)
