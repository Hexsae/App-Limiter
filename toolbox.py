import time
import random
from PyQt5.QtWidgets import *

class Tools():
    def __init__(self, main_window):
        self.main_window = main_window
    
    @staticmethod
    def convert_time(time):
        hours = time//3600
        mins = (time%3600)//60
        secs = (time%3600)%60

        return "{}h {}m {}s".format(hours, mins, secs)

    def start_refresh(self):
        try:
            while self.main_window.running:
                self.main_window.worker.signals.progress.emit(3)
                time.sleep(1)
        except Exception as e:
            print(e)
    
