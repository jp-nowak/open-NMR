import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap, QPolygon, QPen
from PyQt6.QtCore import QPointF, Qt
import numpy as np
import noise
from math import floor
from readingfids import *

def fast_data(data, width, height):
    #normalize
    ymax = max(data[:,1])
    ymin = min(data[:,1])
    data[:,1] = (data[:,1]-ymin)/(ymax-ymin)
    #downsampling
    pointperpixel = 10
    sample = max(len(data)//(pointperpixel*width),1)
    downsampled  = data*(width, height)
    downsampled = downsampled[::sample]
    # for i in range(len(downsampled)):
    #     pt = downsampled.pop(0)
    #     if result: 
    #         if result[-1] != pt : result.append(pt)
    # mask = np.append([True], np.any(np.diff(downsampled, axis=0), axis=1))
    # result = downsampled[mask]
    return downsampled

class spectrum_painter(QWidget):
    def __init__(self, margins, data):
        super().__init__()
        #geometry
        self.data = data
        self.margins = margins
        self.resampled = []

    def paintEvent(self, event):
        #settings
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        #window size
        rect = self.rect()
        size = {
            'w' : rect.topRight().x()-rect.topLeft().x(),
            'h' : rect.bottomLeft().y()-rect.topRight().y()
            }
        self.painter_size = {
            'w' : size['w']-self.margins['right']-self.margins['left'], 
            'h' : size['h']-self.margins['top']-self.margins['bottom']
        }
        painter.translate(self.margins['left'], self.margins['top'])


        #drawing plot
        painter.drawRect(0, 0, self.painter_size['w'], self.painter_size['h'])
        self.resampled = fast_data(data, self.painter_size['w'], self.painter_size['h'])
        print(event)
        for i in range(len(self.resampled)-1): 
            p1 = QPointF(self.resampled[i][0], self.resampled[i][1])
            p2 = QPointF(self.resampled[i+1][0], self.resampled[i+1][1])
            painter.drawLine(p1,p2)
        #painter.drawPolyline(QPolygon([QPointF(x,y) for (x,y) in self.resampled]))
        
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
    y = [noise.pnoise1(x*10) for x in x]
    data = np.column_stack((x, y))
    #main app
    app = QApplication(sys.argv)
    window = window(data)
    window.show()
    sys.exit(app.exec())

