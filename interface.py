import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QPolygonF, QFontMetrics, QFont
from PyQt6.QtCore import QPointF, pyqtSignal, QPoint
import numpy as np
from spectrum import Spectrum_1D
import math


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
    resampled = data[::sample]
    resampled = resampled*(width, height)
    return resampled


class spectrum_painter(QWidget):
    # dragging
    dragStarted = pyqtSignal(QPoint)
    dragEnded = pyqtSignal(QPoint)

    def __init__(self, data, info):
        super().__init__()
        # geometry and settings
        self.textfont = QFont('Times', 10)
        self.data = data
        self.resampled = []
        self.info = info
        self.axpars = {'dlen': 5, 'pixperinc': 50,
                       'incperppm': 2, 'ax_padding': 30, 'spect_padding': 50}
        # deln is a length of delimiter in pixels
        # incperppm: multiples - 2 => 0.5 is the minimum increment
        self.rang = (0, 1)

        # dragging
        self.dragging = False
        self.startPos = QPoint()
        self.endPos = QPoint()

    def mousePressEvent(self, event):
        if self.dragging:
            self.startPos = event.pos()
            self.dragStarted.emit(self.startPos)

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.endPos = event.pos()

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.endPos = event.pos()
            self.dragEnded.emit(self.endPos)

    def paintEvent(self, event):
        print(self.startPos, self.endPos)
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
        fragm = (0, 1)
        self.resampled = data_prep(self.data.copy(
        ), self.p_size['w'], self.p_size['h']-self.axpars['spect_padding'], self.rang)
        self.resampled = [QPointF(i[0], i[1]) for i in self.resampled]
        painter.drawPolyline(QPolygonF(self.resampled))

        # drawing axis delimiters, adjusts automatically
        # parameters
        ax_pos = self.p_size['h']-self.axpars['ax_padding']
        width = self.info['plot_end_ppm']-self.info['plot_begin_ppm']
        incr = math.ceil(self.axpars['incperppm']*width/(self.p_size['w'] //
                         self.axpars['pixperinc']))/self.axpars['incperppm']

        # axis line
        painter.drawLine(QPointF(0.0, ax_pos),
                         QPointF(self.p_size['w'], ax_pos))
        # increments lists
        del_pos_list = [(i*incr+width % incr) /
                        width for i in range(int(width//incr))]
        del_text_list = [str(round((self.info['plot_end_ppm']-i*width) *
                             self.axpars['incperppm'])/self.axpars['incperppm']) for i in del_pos_list]
        # if last delimiter is too close to edge
        if (1-del_pos_list[-1])*self.p_size['w'] < 10:
            del_pos_list.pop(-1)
            del_text_list.pop(-1)
        if del_pos_list[0]*self.p_size['w'] < 10:
            del_pos_list.pop(0)
            del_text_list.pop(0)
        # draw delimiters
        for i in range(len(del_pos_list)):
            del_pos = del_pos_list[i]
            del_text = del_text_list[i]
            top_del = QPointF(
                del_pos*self.p_size['w'], ax_pos+self.axpars['dlen'])
            bot_del = QPointF(
                del_pos*self.p_size['w'], ax_pos-self.axpars['dlen'])
            painter.drawLine(top_del, bot_del)
            # paramters for text
            font_metrics = QFontMetrics(self.textfont)
            text_width = font_metrics.horizontalAdvance(del_text)
            num_pos = QPointF(
                del_pos*self.p_size['w']-0.5*text_width, ax_pos+4*self.axpars['dlen'])
            painter.drawText(num_pos, del_text)

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
        button_layout.addWidget(QPushButton("Reset Zoom"))

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
        self.painter_widget = spectrum_painter(spec.spectrum, spec.info)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.painter_widget)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.painter_widget.mouseReleaseEvent = self.mouse_release_event_handler  # dragging

    def toggle_dragging(self, checked):
        self.painter_widget.dragging = checked

    def mouse_release_event_handler(self, event):
        if self.zoom_button.isChecked():
            self.zoom_button.setChecked(False)


if __name__ == "__main__":
    # main app
    experiments = []
    app = QApplication(sys.argv)
    window = window(experiments)
    window.show()
    sys.exit(app.exec())
