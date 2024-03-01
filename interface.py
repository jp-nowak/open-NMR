import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap, QPolygon
from PyQt6.QtCore import QPoint
import numpy as np
import noise
from scipy.interpolate import interp1d
from math import floor
import matplotlib.pyplot as plt

def fast_data(data, width, height):
    result = []
    ymax = max(data[:,1])
    ymin = min(data[:,1])
    print(ymin, ymax)
    for i in range(width):
        index = floor(len(data)*i/width)
        x, y = data[floor(len(data)*i/width), :]
        y = floor((y-ymin)/(ymax-ymin)*height)
        result.append((i,int(y)))
    return result

class spectrum_painter(QWidget):
    def __init__(self, size, margins, data):
        super().__init__()
        #geometry
        self.margins = margins
        self.painter_size = {
            'w' : size['w']-margins['right']-margins['left'], 
            'h' : size['h']-margins['top']-margins['bottom']
        }
        self.resampled = fast_data(data, self.painter_size['w'], self.painter_size['h'])


    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(self.margins['left'], self.margins['top'])
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
        self.central_widget = spectrum_painter(size, margins, data) 
        self.setCentralWidget(self.central_widget)


if __name__ == "__main__":
    # just simple noise function for testing, np.array for speed
    points = 16000
    x = np.linspace(0, 1, points)
    y = [noise.pnoise1(x*100) for x in x]
    data = np.column_stack((x, y))
    fig, ax = plt.subplots()
    ax.plot(x,y)
    plt.show()
    #main app
    app = QApplication(sys.argv)
    window = window(data)
    window.show()
    sys.exit(app.exec())

