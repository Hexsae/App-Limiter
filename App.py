from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *

from worker import Worker
import toolbox
import sys
import psutil
import json


class Main_UI(QMainWindow):
    def __init__(self):
        super(Main_UI, self).__init__()
        uic.loadUi("ui/App.ui", self)
        self.running = False
        self.Tools = toolbox.Tools(self)
        self.data = {}
        self.item_locations = {} #item row
        self.threadpool = QThreadPool()

        #Initializing save file
        try:
            with open("app_saves.json", "r") as file:
                self.data = json.loads(file.read())
        except:
            with open("app_saves.json", "w") as file:
                file.write("{}")

        self.display_apps(self.data)

        #Defining widgets from .ui file
        self.list_apps = self.findChild(QTableWidget, "list_apps")
        self.addbtn = self.findChild(QPushButton, "addbtn")
        self.deletebtn = self.findChild(QPushButton, "deletebtn")
        self.startbtn = self.findChild(QPushButton, "startbtn")
        self.stopbtn = self.findChild(QPushButton, "stopbtn")
        self.close_appbtn = self.findChild(QPushButton, "close_appbtn")
        self.log_status = self.findChild(QLabel, "log_status")

        #Events
        self.list_apps.itemClicked.connect(self.item_selected)
        self.addbtn.clicked.connect(self.addbtn_clicked)
        self.startbtn.clicked.connect(self.startbtn_clicked)
        self.stopbtn.clicked.connect(self.stopbtn_clicked)
        self.deletebtn.clicked.connect(self.deletebtn_clicked)

        self.addWindow = AddWindow(self)
        self.show()

        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

    #Set running to false when app is closed
    def closeEvent(self, event):
        print("closing..")
        self.running = False
        event.accept()

    def display_apps(self, data):
        if not data:
            return
        for item in data:
            row_count = self.list_apps.rowCount()
            if data[item]["disabled"]:
                time = QTableWidgetItem("Disabled")
            else:
                time = QTableWidgetItem(self.Tools.convert_time(data[item]["time"]))
            self.list_apps.insertRow(row_count)
            self.list_apps.setItem(row_count, 0, QTableWidgetItem(item))
            self.list_apps.setItem(row_count, 1, time)

            #Making time display color red when under 15 mins
            if data[item]["time"] < 900 and not data[item]["disabled"]:
                self.list_apps.item(row_count, 1).setForeground(QColor(255, 0, 0))

            self.list_apps.setItem(row_count, 2, QTableWidgetItem("---"))
            #Save row location of item
            self.item_locations[item] = row_count

    #Event handlers
    def addbtn_clicked(self):
        self.addWindow.show()
        self.addWindow.load_processes()
    
    def item_selected(self):
        if self.running: return
        self.deletebtn.setEnabled(True)
    
    def deletebtn_clicked(self):
        try:
            row = self.list_apps.currentRow()
            if row < 0: return

            item_name = self.list_apps.item(row, 0).text()
            self.data.pop(item_name)

            with open("app_saves.json", "w") as file:
                file.write(json.dumps(self.data))

            self.list_apps.removeRow(self.item_locations[item_name])
            #Updating item_locations 
            self.item_locations = dict(zip(self.data, list(range(0,self.list_apps.rowCount()))))

        except Exception as e:
            print(e)
    
    def handle_progress(self):
        try:
            processes = list(set(map(lambda x: x.name(), psutil.process_iter())))
            for item in self.data:
                row = self.item_locations[item]
                status = "Running..." if item in processes else "closed"

                if not self.data[item]["disabled"] and self.data[item]["time"] != 0:
                    self.data[item]["time"] -= 1
                    time = self.Tools.convert_time(self.data[item]["time"])
                    self.list_apps.setItem(row, 0, QTableWidgetItem(item))
                    self.list_apps.setItem(row, 1, QTableWidgetItem(time))
                    self.list_apps.setItem(row, 2, QTableWidgetItem(status))

                    #Setting colors
                    if self.data[item]["time"] < 900:
                        print(row)
                        self.list_apps.item(row, 1).setForeground(QColor(255, 0, 0))
                    if status == "Running...":
                        self.list_apps.item(row, 2).setForeground(QColor(0, 200, 0))

                self.update()
        except Exception as e:
            print(e)

    def startbtn_clicked(self):
        try:
            self.stopbtn.setEnabled(True)
            self.startbtn.setDisabled(True)
            self.running = True
            self.worker = Worker(self.Tools.start_refresh)

            self.worker.signals.progress.connect(self.handle_progress)

            self.threadpool.start(self.worker)
            self.deletebtn.setDisabled(True)
            self.log_status.setText("ON")
            self.log_status.setStyleSheet("color: green")
        except Exception as e:
            print(e)

    def stopbtn_clicked(self):
        self.stopbtn.setEnabled(False)
        self.startbtn.setDisabled(False)
        self.running = False
        self.log_status.setText("OFF")
        self.log_status.setStyleSheet("color: red")

        #Enabling edit and delete buttons if an item is selected
        if self.list_apps.currentRow():
            self.deletebtn.setEnabled(True)

class AddWindow(QMainWindow):
    def __init__(self, main_window):
        super(AddWindow, self).__init__()
        uic.loadUi("ui/AddWindow.ui", self)
        self.main_window = main_window

        self.open_apps = self.findChild(QComboBox, "open_apps")
        self.time_hour = self.findChild(QSpinBox, "time_hour")
        self.time_min = self.findChild(QSpinBox, "time_min")
        self.confirmbtn = self.findChild(QPushButton, "confirmbtn")

        self.confirmbtn.clicked.connect(self.confirm_clicked)
    
    def confirm_clicked(self):
        time_hour = int(self.time_hour.cleanText())
        time_min = int(self.time_min.cleanText())
        time_secs = (time_hour * 3600) + (time_min * 60)
        converted = self.main_window.Tools.convert_time(time_secs)
        disabled = False
        app_name = self.open_apps.currentText()

        if not app_name:
            return print("No app selected")
        
        if time_secs == 0:
            disabled = True

        response = QMessageBox.question(self, "App Limiter", "Confirm?", QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.No:
            return

        with open("app_saves.json", "w") as file:
            self.main_window.data[app_name] = {
                "time": time_secs,
                "disabled": disabled
            }
            output = json.dumps(self.main_window.data)
            file.write(output)
            
        #Inserting app to the table
        row_count = self.main_window.list_apps.rowCount()
        self.main_window.list_apps.insertRow(row_count)
        self.main_window.list_apps.setItem(row_count, 0, QTableWidgetItem(app_name))
        self.main_window.list_apps.setItem(row_count, 1, QTableWidgetItem(converted))
        self.main_window.list_apps.setItem(row_count, 2, QTableWidgetItem("---"))

        #save item location
        self.main_window.item_locations[app_name] = row_count

        self.close()
                
    #setup
    def load_processes(self):
        processes = list(set(map(lambda x: x.name(), psutil.process_iter())))
        processes = sorted(processes, key=str.casefold)
        processes.insert(0, "")
        self.open_apps.clear()
        self.open_apps.addItems(processes)


app = QApplication(sys.argv)
Main = Main_UI()
app.exec_()
