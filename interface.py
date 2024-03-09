import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QPointF
import numpy as np
from spectrum import Spectrum_1D

def data_prep(data, width, height, range):
    data = data[round(len(data)*range[0]):round(len(data)*range[1])]
    data = np.column_stack((np.linspace(0,1,len(data)), data))
    #normalize
    ymax = max(data[:,1])
    ymin = min(data[:,1])
    data[:,1] = -(data[:,1]-ymin)/(ymax-ymin)+1
    #downsampling, bad method, we need one for nmr spectra specifically
    pointperpixel = 4
    sample = max(len(data)//(pointperpixel*width),1)
    
    #scaling to image size
    resampled = data[::sample]
    resampled = resampled*(width, height)
    return resampled

class spectrum_painter(QWidget):
    def __init__(self, data, info):
        super().__init__()
        #geometry
        self.data = data
        self.resampled = []
        self.info = info
        print(info)

    def paintEvent(self, event):
        # settings
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # updating window size
        rect = self.rect()
        self.p_size = {
            'w' : rect.topRight().x()-rect.topLeft().x(),
            'h' : rect.bottomLeft().y()-rect.topRight().y()
            }
        #drawing plot
        fragm = (0,1)
        self.resampled = data_prep(self.data.copy(), self.p_size['w'], 0.8*self.p_size['h'], fragm)
        for i in range(len(self.resampled)-1):
            p1 = QPointF(self.resampled[i][0], self.resampled[i][1])
            p2 = QPointF(self.resampled[i+1][0], self.resampled[i+1][1])
            painter.drawLine(p1,p2)
        
        #drawing range
        bot_padding = 0.9*self.p_size['h']
        tup_size = 5
        painter.drawLine(QPointF(0.0, bot_padding), QPointF(self.p_size['w'], bot_padding))
        width = self.info['plot_end_ppm']-self.info['plot_begin_ppm']
        delimiter_tup = [(float(i)+self.info['plot_begin_ppm']%1)/width for i in range(int(width//1))]
        for incr in delimiter_tup:
            top_del = QPointF(incr*self.p_size['w'],bot_padding+tup_size)
            bot_del = QPointF(incr*self.p_size['w'],bot_padding-tup_size)
            painter.drawLine(top_del, bot_del)
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
        self.setGeometry(200, 200, size['w'], size['h']) 
        
        # opening spectrum, in the future on event
        experiments = []
        title = "Open NMR"
        if 'event':
            nmr_file_path = "./example_fids/agilent_example1H.fid"
            experiments.append(Spectrum_1D.create_from_file(nmr_file_path))
            title+= ' - ' + nmr_file_path
        
        # modifying in relation to spectrum
        self.setWindowTitle(title)
        spec = experiments[0]
        self.painter_widget = spectrum_painter(spec.spectrum, spec.info)
        layout.addWidget(self.painter_widget)

        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    #main app
    experiments = []
    app = QApplication(sys.argv)
    window = window(experiments)
    window.show()
    sys.exit(app.exec())

