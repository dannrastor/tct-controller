from PyQt5.QtCore import QObject, pyqtSignal


class AsyncWorker(QObject):
    finished = pyqtSignal()

    has_dialog = False
    dialog = None
    description = 'Virtual class'

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings

    def run(self):
        self.action()
        self.finished.emit()

    def action(self):
        # Overload this with your long task
        # You'd better update core.measurement_state while it runs
        pass