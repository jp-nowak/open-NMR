import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap, QPolygon
from PyQt6.QtCore import QPoint
import numpy as np
import noise
from math import floor

def fast_data(data, width, height):
    # this is very primitive and fast
    # the value closest to a pixel is chosen
    result = []
    ymax = max(data[:,1])
    ymin = min(data[:,1])
    print(ymin, ymax)
    for i in range(width):
        y = data[floor(len(data)*i/width), :][1]
        y = floor((y-ymin)/(ymax-ymin)*height)
        result.append((i,int(y)))
    return result

class spectrum_painter(QWidget):
    def __init__(self, margins, data):
        super().__init__()
        #geometry
        self.data = data
        self.margins = margins
        
        

    def paintEvent(self, event):
        rect = self.rect()
        size = {
            'w' : rect.topRight().x()-rect.topLeft().x(),
            'h' : rect.bottomLeft().y()-rect.topRight().y()
            }
        self.painter_size = {
            'w' : size['w']-self.margins['right']-self.margins['left'], 
            'h' : size['h']-self.margins['top']-self.margins['bottom']
        }
        self.resampled = fast_data(data, self.painter_size['w'], self.painter_size['h'])
        painter = QPainter(self)
        painter.translate(self.margins['left'], self.margins['top'])
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        print(event)
        #painter.setPen(QColor(0, 0, 255))  # color
        painter.drawRect(0, 0, self.painter_size['w'], self.painter_size['h'])
        painter.drawPolyline(QPolygon([QPoint(x,y) for (x,y) in self.resampled]))
        painter.end()

class window(QMainWindow):
    def __init__(self, data):
        super().__init__()
        size = {'w':800,'h':400}
        margins = {'top':80, 'left':80, 'bottom':10, 'right':10}
        self.setGeometry(200, 200, size['w'], size['h']) #placement, windowsize
        self.setWindowTitle("Open NMR")
        self.central_widget = spectrum_painter(margins, data)
        self.setCentralWidget(self.central_widget)


if __name__ == "__main__":
    # just simple noise function for testing, np.array for speed
    points = 16000
    x = np.linspace(0, 1, points)
    y = [noise.pnoise1(x*100) for x in x]
    data = np.column_stack((x, y))
    #main app
    app = QApplication(sys.argv)
    window = window(data)
    window.show()
    sys.exit(app.exec())

