import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QPointF
import numpy as np
from spectrum import Spectrum_1D

def open_fid(nmr_file_path):
    #this is something that class should do
    with open(nmr_file_path, "rb") as file:
        file_content = file.read()
    exp = Spectrum_1D.create_from_file(file_content, "agilent")
    return exp

def fix_spectrum(spect):
    data = np.column_stack((np.linspace(0,1,len(spect)), spect))
    return data

def fast_data(data, width, height):
    #normalize
    ymax = max(data[:,1])
    ymin = min(data[:,1])
    data[:,1] = -(data[:,1]-ymin)/(ymax-ymin)+1
    #downsampling, bad method, we need one for nmr spectra specifically
    pointperpixel = 100
    sample = max(len(data)//(pointperpixel*width),1)
    resampled = data*(width, height)
    resampled = resampled[::sample]
    return resampled

class spectrum_painter(QWidget):
    def __init__(self, margins, data):
        super().__init__()
        #geometry
        self.data = data
        self.margins = margins
        self.resampled = []

    def paintEvent(self, event):
        # settings
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # updating window size
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
        self.resampled = fast_data(self.data.copy(), self.painter_size['w'], self.painter_size['h'])
        for i in range(len(self.resampled)-1):
            p1 = QPointF(self.resampled[i][0], self.resampled[i][1])
            p2 = QPointF(self.resampled[i+1][0], self.resampled[i+1][1])
            painter.drawLine(p1,p2)
        
        painter.end()

class window(QMainWindow):
    def __init__(self, experiments):
        super().__init__()
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.button = QPushButton("Open File")
        layout.addWidget(self.button)
        self.button = QPushButton("Find Peaks")
        layout.addWidget(self.button)

        # widnow size, position, margins, etc
        size = {'w':800,'h':400}
        margins = {'top':10, 'left':10, 'bottom':10, 'right':10}
        self.setGeometry(200, 200, size['w'], size['h']) 
        
        # opening spectrum, in the future on event
        experiments = []
        title = "Open NMR"
        if 'event':
            nmr_file_path = "fid"
            experiments.append(open_fid(nmr_file_path))
            title+= ' - ' + nmr_file_path
        
        # modifying in relation to spectrum
        self.setWindowTitle(title)
        data = fix_spectrum(experiments[0].spectrum)

        self.painter_widget = spectrum_painter(margins, data)
        layout.addWidget(self.painter_widget)

        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    #main app
    experiments = []
    app = QApplication(sys.argv)
    window = window(experiments)
    window.show()
    sys.exit(app.exec())

