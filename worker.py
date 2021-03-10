from PyQt5.QtCore import *
import traceback
import sys

class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
     def __init__(self, func):
        super(Worker, self).__init__()
        self.func = func
        self.signals = WorkerSignals()

     @pyqtSlot()
     def run(self):
        try:
            result = self.func()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
 
