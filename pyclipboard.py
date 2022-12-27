import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QGridLayout, QPushButton,\
     QWidget, QScrollArea, QToolBar, QAction, QStatusBar, QDialog, QDialogButtonBox, \
     QLabel, QSpinBox, QSystemTrayIcon, QMenu, QCheckBox)
import textwrap
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QIcon
import json
import os

class ClipboardEx(QMainWindow):

    #class for one record which is handled as a button
    class ClipboardRecord(QPushButton):
        
            def __init__(self, copiedText):
                QPushButton.__init__(self)
                self.recordText = copiedText #copy of the text
                self.setFixedSize(270, 80)
                self.setStyleSheet("QPushButton { text-align: left; padding:3px; vertical-align:top}")
                #shorten the long text
                self.setText(textwrap.fill(textwrap.shorten(self.recordText,150),30))
                self.clicked.connect(self.copy_to_clipboard)

            def copy_to_clipboard(self):
                #to handle the situation with an empty clipboard
                if self.recordText != "": 
                    QApplication.clipboard().setText(self.recordText)

            def remove_from_UI(self):
                self.setParent(None)
                self.deleteLater()

    #user class for 'Settings' dialog. The user can set up a max number of records to be stored in app
    class dialogSettings(QDialog):
        def __init__(self, dictSettings, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Settings")
            self.buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            self.buttonBox.accepted.connect(self.accept)
            self.buttonBox.rejected.connect(self.reject)
            self.numberOfRecords = dictSettings['maxNrOfRecords']
            self.mainLayout = QVBoxLayout()
            self.dataLayout = QGridLayout()
            self.mainLayout.addLayout(self.dataLayout)
            self.spin = QSpinBox()
            self.spin.setRange(1, 30)
            self.spin.setValue(self.numberOfRecords)
            self.spin.valueChanged.connect(self.spin_value_changed)

            self.chkMinimized = QCheckBox()
            self.chkMinimized.setCheckState(dictSettings['startMinimized'])
            self.chkMinimized.stateChanged.connect(self.chkMinimized_value_changed)

            self.dataLayout.addWidget(QLabel("Number of records to be stored: "), 0, 0)
            self.dataLayout.addWidget(self.spin, 0, 1)
            self.dataLayout.addWidget(QLabel("Start minimized: "), 1, 0)
            self.dataLayout.addWidget(self.chkMinimized, 1, 1)
            self.mainLayout.addWidget(self.buttonBox)
            self.setLayout(self.mainLayout)

        def spin_value_changed(self):
            self.numberOfRecords = self.spin.value()

        def chkMinimized_value_changed(self, s):
            self.startMin = s

    #body of the main class    
    def __init__(self):
        super().__init__()

        self.scriptDir = os.path.realpath(os.path.dirname(__file__))
        self.configFilePath = os.path.join(self.scriptDir, "config.txt")
        

        self.appSettingsDict = {'maxNrOfRecords' : 5, 'startMinimized': Qt.Checked}
        self.read_settings()
        self.recordList = [] #the list of all records buttons
               
        self.initialize_UI()

    def read_settings(self):
        try:
            file = open(self.configFilePath, "r")
            data = json.load(file)
            for key in self.appSettingsDict:
                try:
                    self.appSettingsDict[key] = data[key]
                except:
                    pass
                
        except FileNotFoundError:
            print("INFO: config file could not be found, a new one has been created")
            self.write_settings()

        except json.decoder.JSONDecodeError:
            print("INFO: config file was corrupted, default values were written")
            self.write_settings()

    def write_settings(self):
        with open(self.configFilePath, "w") as file:
                file.write(json.dumps(self.appSettingsDict))


    def initialize_UI(self):
        self.setWindowTitle("Py_Clipboard")
        self.setFixedSize(300,450)
        #source for icons: https://www.elegantthemes.com/blog/freebie-of-the-week/beautiful-flat-icons-for-free
        self.deleteAllIcon = QIcon(os.path.join(self.scriptDir, "images", "delete-all.png"))
        self.settingsIcon = QIcon(os.path.join(self.scriptDir, "images", "settings.png"))
        self.mainWindowIcon = QIcon(os.path.join(self.scriptDir, "images", "main-window.png"))
        self.setWindowIcon(self.mainWindowIcon)

        self.appStatusBar = QStatusBar()
        self.setStatusBar(self.appStatusBar)
        self.set_tray()
        self.create_toolbar()

        #organize widgets vertically
        self.winVlayout = QVBoxLayout()
        self.winVlayout.setContentsMargins(10,10,10,10)
        self.winVlayout.setAlignment(Qt.AlignTop)
        
        mainWidget = QWidget(self)
        
        #make the main window scrollable
        self.winScroll = QScrollArea()
        self.winScroll.setWidgetResizable(True)
        self.winScroll.setWidget(mainWidget)
        self.setCentralWidget(self.winScroll)

        mainWidget.setLayout(self.winVlayout)
               
        #connect app with the system clipboard. New fragments will be added automatically
        #when the user copies any text
        self.appClipboard = QApplication.clipboard()
        if self.appClipboard.text != "":
            self.copy_from_clipboard()
        self.appClipboard.dataChanged.connect(self.copy_from_clipboard)
        
        self.show()
        if self.appSettingsDict['startMinimized'] == Qt.Checked:
            self.setWindowState(Qt.WindowMinimized)
            
        else:
            self.setWindowState(Qt.WindowNoState)
    
    def set_tray(self):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.mainWindowIcon)
        self.tray.setVisible(False)
        self.appMenu = QMenu()
        self.actionQuit = QAction("Quit")
        self.actionQuit.triggered.connect(QApplication.quit)
        self.actionShow = QAction("Show")
        self.actionShow.triggered.connect(lambda: self.setWindowState(Qt.WindowNoState))
        
        self.appMenu.addAction(self.actionShow)
        self.appMenu.addAction(self.actionQuit)

        self.tray.setContextMenu(self.appMenu)

        self.tray.activated.connect(lambda: self.setWindowState(Qt.WindowNoState))

    
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() == Qt.WindowMinimized:
                
                self.tray.setVisible(True)
                self.hide()
                event.ignore()
            elif self.windowState() == Qt.WindowNoState:
                self.tray.setVisible(False)
                #self.show()
                self.showNormal()
                
            

    def create_toolbar(self):
        #create the toolbar
        self.appToolBar = QToolBar("App Toolbar")
        self.appToolBar.setIconSize(QSize(32, 32))
        self.addToolBar(self.appToolBar)

        #add the tool button for 'Clear all' option
        self.delete_all_records = QAction(self.deleteAllIcon, "Delete all", self)
        self.delete_all_records.setStatusTip("Delete all fragments from the app memory")
        self.delete_all_records.triggered.connect(self.clear_app_memory)     
        self.appToolBar.addAction(self.delete_all_records)
        
        #add the tool button for 'Settings' option
        self.settings = QAction(self.settingsIcon, "Settings", self)
        self.settings.setStatusTip("App settings")
        self.settings.triggered.connect(self.adjust_settings)

        self.appToolBar.addAction(self.settings)
        self.setStatusBar(QStatusBar(self))

    
    def adjust_settings(self):
        dlg = self.dialogSettings(self.appSettingsDict, self)
        if dlg.exec():
            self.appSettingsDict['maxNrOfRecords'] = dlg.numberOfRecords
            self.appSettingsDict['startMinimized'] = dlg.startMin
            self.write_settings()
            
            

    def clear_app_memory(self):
        #delete all records in the app memory
        while len(self.recordList) > 0:
            self.recordList.pop(0).remove_from_UI()
        

    def copy_from_clipboard(self):
        mimeData = self.appClipboard.mimeData()
        #work only with text
        if mimeData.hasText():

            if mimeData.text () != "": #if the clipboard is not empty

                #delete the oldest record basing on FIFO principle
                if len(self.recordList) == self.appSettingsDict['maxNrOfRecords']:
                    self.recordList.pop(0).remove_from_UI()

                #add the new record to the app
                self.recordList.append(self.ClipboardRecord(mimeData.text()))
                self.winVlayout.insertWidget(0, self.recordList[len(self.recordList)-1] ,alignment=Qt.AlignTop)   
                self.setWindowState(Qt.WindowMinimized)  
        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Oxygen')

    

    window = ClipboardEx()

    

    sys.exit(app.exec_())