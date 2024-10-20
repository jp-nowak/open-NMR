from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget)
from PyQt5.QtCore import pyqtSlot

POWERS_OF_TWO = (# '1', 
                 # '2', 
                 # '4', 
                 # '8', 
                 # '16', 
                 # '32', 
                 # '64', 
                 # '128', 
                 # '256', 
                 # '512', 
                 '1024', 
                 '2048', 
                 '4096', 
                 '8192', 
                 '16384', 
                 '32768', 
                 '65536', 
                 '131072', 
                 '262144', 
                 '524288', 
                 '1048576', 
                 '2097152', 
                 # '4194304', 
                 # '8388608', 
                 # '16777216', 
                 # '33554432', 
                 # '67108864', 
                 # '134217728', 
                 # '268435456', 
                 # '536870912', 
                 # '1073741824', 
                 # '2147483648', 
                 # '4294967296', 
                 # '8589934592',
                 )

class ZeroFillingAndTruncatingWindow(QWidget):
    
    def __init__(self, parent, current_tab):
        super().__init__(parent, QtCore.Qt.Window)
        
        current_tab.window().tabs_frame.selectedSpectrumSignal.connect(self.change_active_spectrum)
        
        self.list_widget = QListWidget(self)
        self.list_widget.addItems(POWERS_OF_TWO)
        self.list_widget.currentRowChanged.connect(self.changed_value)
        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        
        self.change_active_spectrum(current_tab)
        
    @pyqtSlot(object)
    def change_active_spectrum(self, new_active_tab): 
        self.current_tab = new_active_tab
        self.setWindowTitle(f"""Zero Filling/Truncating: {self.current_tab.experiment.info["samplename"]}""")
        self.list_widget.setCurrentRow(POWERS_OF_TWO.index(str(len(self.current_tab.experiment.spectrum))))        
        
    @pyqtSlot(int)
    def changed_value(self, nrow):
        new_value = POWERS_OF_TWO[nrow]
        if int(new_value) > len(self.current_tab.experiment.spectrum):
            self.current_tab.experiment.restore_fid()
            self.current_tab.experiment.zero_to_number(int(new_value))
        elif int(new_value) < len(self.current_tab.experiment.spectrum):
            self.current_tab.experiment.truncate_to_number(int(new_value))
        
        self.current_tab.refresh()
        