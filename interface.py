import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt

class spectrum_painter(QWidget):
    def __init__(self, size, margins):
        super().__init__()
        self.painter_size = {
            'w' : size['w']-margins['right']-margins['left'], 
            'h' : size['h']-margins['top']-margins['bottom']
        }
        self.margins = margins
        self.pixmap = QPixmap(self.painter_size['w'], self.painter_size['h'])
    
    def paintEvent(self, margin):
        painter = QPainter(self)
        #painter.setPen(QColor(0, 0, 255))  # color
        painter.drawRect(self.margins['left'], self.margins['top'], self.painter_size['w'], self.painter_size['h'])
        painter.end()
        painter.drawPixmap(self.margins['left'], self.margins['top'], self.pixmap) 

class window(QMainWindow):
    def __init__(self):
        super().__init__()
        size = {'w':800,'h':400}
        margins = {'top':80, 'left':80, 'bottom':10, 'right':10}
        self.setGeometry(200, 200, size['w'], size['h']) #placement, windowsize
        self.setWindowTitle("Open NMR") 
        self.central_widget = spectrum_painter(size, margins) 
        self.setCentralWidget(self.central_widget)

if __name__ == "__main__":
    filename = 'fid'
    app = QApplication(sys.argv)
    window = window()
    window.show()
    sys.exit(app.exec())

