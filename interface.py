import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtGui import QMouseEvent, QPainter, QPolygonF, QFontMetrics, QFont
from PyQt6.QtCore import QPointF, pyqtSignal, QPoint
import numpy as np
from spectrum import Spectrum_1D
import math


def axis_generator(painter, p_size, axis_pars, textfont):
    # drawing axis delimiters, adjusts automatically
    # parameters
    ax_pos = p_size['h']-axis_pars['ax_padding']
    width = axis_pars['end_ppm']-axis_pars['begin_ppm']
    incr = math.ceil(axis_pars['incperppm']*width/(p_size['w'] //
                                                   axis_pars['pixperinc']))/axis_pars['incperppm']

    # axis line
    painter.drawLine(QPointF(0.0, ax_pos),
                     QPointF(p_size['w'], ax_pos))
    # increments lists
    del_pos_list = [(i*incr+width % incr) /
                    width for i in range(int(width//incr))]
    del_text_list = [str(round((axis_pars['end_ppm']-i*width) *
                               axis_pars['incperppm'])/axis_pars['incperppm']) for i in del_pos_list]
    # if last delimiter is too close to edge
    if (1-del_pos_list[-1])*p_size['w'] < 10:
        del_pos_list.pop(-1)
        del_text_list.pop(-1)
    if del_pos_list[0]*p_size['w'] < 10:
        del_pos_list.pop(0)
        del_text_list.pop(0)
    # draw delimiters
    for i in range(len(del_pos_list)):
        del_pos = del_pos_list[i]
        del_text = del_text_list[i]
        top_del = QPointF(
            del_pos*p_size['w'], ax_pos+axis_pars['dlen'])
        bot_del = QPointF(
            del_pos*p_size['w'], ax_pos-axis_pars['dlen'])
        painter.drawLine(top_del, bot_del)
        # paramters for text
        font_metrics = QFontMetrics(textfont)
        text_width = font_metrics.horizontalAdvance(del_text)
        num_pos = QPointF(
            del_pos*p_size['w']-0.5*text_width, ax_pos+4*axis_pars['dlen'])
        painter.drawText(num_pos, del_text)


def data_prep(data, width, height, rang):
    data = data[round(len(data)*rang[0]):round(len(data)*rang[1])]
    data = np.column_stack((np.linspace(0, 1, len(data)), data))
    # normalize
    ymax = max(data[:, 1])
    ymin = min(data[:, 1])
    data[:, 1] = -(data[:, 1]-ymin)/(ymax-ymin)+1
    # downsampling, bad method, we need one for nmr spectra specifically
    pointperpixel = 100
    sample = max(len(data)//(pointperpixel*width), 1)

    # scaling to image size
    data = data[::sample]*(width, height)
    return data


class spectrum_painter(QWidget):
    # dragging
    # dragStarted = pyqtSignal(0.0)
    # dragEnded = pyqtSignal(0.0)

    def __init__(self, data, info, zoom_button):
        super().__init__()
        self.zoom_button = zoom_button
        # geometry and settings
        self.textfont = QFont('Times', 10)
        self.data = data
        self.resampled = []
        self.info = info
        self.axis_pars = {'dlen': 5, 'pixperinc': 50,
                          'incperppm': 10, 'ax_padding': 30, 'spect_padding': 50,
                          'end_ppm': self.info['plot_end_ppm'],
                          'begin_ppm': self.info['plot_begin_ppm']}
        # deln is a length of delimiter in pixels
        # incperppm: multiples - 2 => 0.5 is the minimum increment
        self.rang = [0, 1]

        # dragging
        self.dragging = False
        self.startPos = 0
        self.endPos = 1

    def mousePressEvent(self, event):
        if self.dragging:
            self.startPos = event.pos().x()/self.p_size['w']

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.endPos = event.pos().x()/self.p_size['w']

    def mouseReleaseEvent(self, event):
        #adjusting rang
        zoomrang = [self.endPos, self.startPos]
        zoomrang.sort()
        self.rang = [self.rang[0]+(self.rang[1]-self.rang[0])*zoomrang[0],
                     self.rang[0]+(self.rang[1]-self.rang[0])*zoomrang[1]
                     ]
        self.rang.sort()
        if self.zoom_button.isChecked():
            self.zoom_button.setChecked(False)
        #adjusting axis
        width = self.info['plot_end_ppm']-self.info['plot_begin_ppm']
        self.axis_pars['end_ppm'] = self.info['plot_end_ppm']-width*self.rang[0]
        self.axis_pars['begin_ppm'] = self.info['plot_begin_ppm']+width*(1-self.rang[1])
        self.update()


    def paintEvent(self, event):

        # settings
        painter = QPainter(self)
        painter.setFont(self.textfont)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # updating window size
        rect = self.rect()
        self.p_size = {
            'w': rect.topRight().x()-rect.topLeft().x(),
            'h': rect.bottomLeft().y()-rect.topRight().y()
        }
        # drawing plot
        self.resampled = data_prep(self.data.copy(),
                                   self.p_size['w'],
                                   self.p_size['h'] -
                                   self.axis_pars['spect_padding'],
                                   self.rang)
        self.resampled = [QPointF(i[0], i[1]) for i in self.resampled]
        painter.drawPolyline(QPolygonF(self.resampled))

        axis_generator(painter, self.p_size, self.axis_pars, self.textfont)

        painter.end()


class window(QMainWindow):
    def __init__(self, experiments):
        super().__init__()

        button_layout = QHBoxLayout()
        button_layout.addWidget(QPushButton("Open File"))
        button_layout.addWidget(QPushButton("Find Peaks"))
        
        self.zoom_button = QPushButton("Zoom")
        self.zoom_button.setCheckable(True)
        self.zoom_button.toggled.connect(self.toggle_dragging)
        button_layout.addWidget(self.zoom_button)
        
        self.zoom_reset_button = QPushButton("Reset Zoom")
        self.zoom_reset_button.clicked.connect(self.reset_zoom)
        button_layout.addWidget(self.zoom_reset_button)

        # widnow size, position, margins, etc
        size = {'w': 800, 'h': 400}
        self.setGeometry(200, 200, size['w'], size['h'])

        # opening spectrum, in the future on event
        experiments = []
        title = "Open NMR"
        if 'event':
            nmr_file_path = "./example_fids/agilent_example1H.fid"
            experiments.append(Spectrum_1D.create_from_file(nmr_file_path))
            title += ' - ' + nmr_file_path

        # modifying in relation to spectrum
        self.setWindowTitle(title)
        spec = experiments[0]
        self.painter_widget = spectrum_painter(
            spec.spectrum, spec.info, self.zoom_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.painter_widget)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def toggle_dragging(self, checked):
        self.painter_widget.dragging = True
    
    def reset_zoom(self):
        self.painter_widget.rang = [0,1]
        self.painter_widget.startPos = 0
        self.painter_widget.endPos = 1
        self.painter_widget.axis_pars['begin_ppm'] = self.painter_widget.info['plot_begin_ppm']
        self.painter_widget.axis_pars['end_ppm'] = self.painter_widget.info['plot_end_ppm']
        self.painter_widget.update()


if __name__ == "__main__":
    # main app
    experiments = []
    app = QApplication(sys.argv)
    window = window(experiments)
    window.show()
    sys.exit(app.exec())
