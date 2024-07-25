from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget)
from PyQt5.QtCore import pyqtSlot
POWERS_OF_TWO = (#1, 
                 # 2, 
                 # 4, 
                 # 8, 
                 # 16, 
                 # 32, 
                 # 64, 
                 # 128, 
                 # 256, 
                 # 512, 
                 1024, 
                 2048, 
                 4096, 
                 8192, 
                 16384, 
                 32768, 
                 65536, 
                 131072, 
                 262144, 
                 524288, 
                 1048576, 
                 2097152, 
                 # 4194304, 
                 # 8388608, 
                 # 16777216, 
                 # 33554432, 
                 # 67108864, 
                 # 134217728, 
                 # 268435456, 
                 # 536870912, 
                 # 1073741824, 
                 # 2147483648, 
                 # 4294967296, 
                 # 8589934592,
                 )

class ZeroFillingAndTruncatingWindow(QWidget):
    
    def __init__(self, current_tab):
        super().__init__()
        
        self.current_tab = current_tab
        self.current_tab.window().tabs_frame.selectedSpectrumSignal.connect(self.change_active_spectrum)
        self.setWindowTitle(f"""Zero Filling/Truncating: {self.current_tab.experiment.info["samplename"]}""")
        
        list_widget = QListWidget(self)
        list_widget.addItems((str(i) for i in POWERS_OF_TWO))
        
        layout = QVBoxLayout()
        layout.addWidget(list_widget)
        
        self.setLayout(layout)
        
    @pyqtSlot(object)
    def change_active_spectrum(self, new_active_tab): 
        pass
        