import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

class spectrum_painter(QWidget):
    def __init__(self):
        super().__init__()

    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.setPen(QColor(0, 0, 255))  # color
        painter.drawLine(50, 100, 200, 100)

class window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(200, 200, 800, 400) #placement, windowsize
        self.setWindowTitle("Open NMR") 
        self.central_widget = spectrum_painter() 
        self.setCentralWidget(self.central_widget)

if __name__ == "__main__":
    filename = 'fid'
    app = QApplication(sys.argv)
    window = window()
    window.show()
    sys.exit(app.exec())

