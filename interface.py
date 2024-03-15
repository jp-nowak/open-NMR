import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QStyleFactory
from PyQt6.QtGui import QMouseEvent, QPainter, QPolygonF, QFontMetrics, QFont, QFontDatabase
from PyQt6.QtCore import QPointF, pyqtSignal, QPoint
import numpy as np
from spectrum import Spectrum_1D
import math


def axis_generator(painter, p_size, axis_pars, textfont):
    # drawing axis delimiters, adjusts automatically
    # parameters
    ax_pos = p_size['h']-axis_pars['ax_padding']
    width = axis_pars['end_ppm']-axis_pars['begin_ppm']
    incr_ppm = 2**round(np.log2(width*axis_pars['pixperinc']/math.ceil(p_size['w'])))
    incr_fac = incr_ppm/width
    # axis line
    painter.drawLine(QPointF(0.0, ax_pos),
                     QPointF(p_size['w'], ax_pos))
    print(incr_ppm)
    # increments lists
    del_pos_list = []
    if axis_pars['end_ppm'] > 0 and axis_pars['begin_ppm'] < 0:
        numincright = math.ceil(axis_pars['end_ppm']/incr_ppm)
        del_pos_list = [axis_pars['end_ppm']/width-i*incr_fac for i in range(numincright)]
        # negative_list = [i*incr_ppm/width+abs(1-axis_pars['begin_ppm']/width) for i in range(math.ceil(abs(axis_pars['begin_ppm']/incr_ppm)))]
        # del_pos_list.extend(negative_list)
    else:
        del_pos_list = [axis_pars['end_ppm']%incr_ppm/width+i*incr_fac for i in range(math.ceil(width/incr_ppm))]
    del_pos_list.sort()
    del_pos_list = [i for i in del_pos_list if i>0+20/p_size['w'] and i<1-20/p_size['w']]
    print(del_pos_list)
    del_text_list = [str(round(axis_pars['end_ppm']-i*width, 3)) for i in del_pos_list]

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
    data = data*(width, height)
    new_method = True
    if not new_method:
        # downsampling, bad method, we need one for nmr spectra specifically
        pointperpixel = 100
        sample = max(len(data)//(pointperpixel*width), 1)
        # scaling to image size
        resampled = data[::sample]
        return resampled
    if new_method:
        resampled = []
        sample = int(len(data)//(width*2))
        if sample<4:
            return data
        for pix in range(int(math.ceil(len(data)/sample))):
            start = pix*sample
            end = min((pix+1)*sample-1, len(data)-1)
            if abs(max(data[start:end, 1])-min(data[start:end, 1])) > 1:
                resampled.extend(data[start:end])
            else:
                resampled.extend([data[start], data[end]])
        return resampled
            



class spectrum_painter(QWidget):
    def __init__(self, zoom_button, integrate_button):
        super().__init__()
        self.zoom_button = zoom_button
        self.integrate_button = integrate_button
        self.drawstatus = False
        self.textfont = QFont('Times', 10)

    def generate_data(self, experiment):
        # data
        self.drawstatus = True
        self.experiment = experiment
        self.data = experiment.spectrum
        self.info = experiment.info
        self.resampled = []
        self.axis_pars = {'dlen': 5, 'pixperinc': 70,
                          'incperppm': 100, 'ax_padding': 30, 'spect_padding': 50,
                          'end_ppm': self.info['plot_end_ppm'],
                          'begin_ppm': self.info['plot_begin_ppm']}
        # deln is a length of delimiter in pixels
        # incperppm: multiples - 2 => 0.5 is the minimum increment
        self.rang = [0, 1]

        # dragging
        self.zooming = False
        self.integrating = False
        self.startPos = 0
        self.endPos = 1

    def mousePressEvent(self, event):
        if self.zooming or self.integrating:
            self.startPos = event.pos().x()/self.p_size['w']

    def mouseMoveEvent(self, event):
        if self.zooming or self.integrating:
            self.endPos = event.pos().x()/self.p_size['w']

    def mouseReleaseEvent(self, event):
        # adjusting rang
        selrang = [self.endPos, self.startPos]
        selrang.sort()
        absrang = [self.rang[0]+(self.rang[1]-self.rang[0])*selrang[0],
                   self.rang[0]+(self.rang[1]-self.rang[0])*selrang[1]
                   ]
        absrang.sort()
        if self.zooming:
            self.rang = absrang
            # adjusting axis
            width = self.info['plot_end_ppm']-self.info['plot_begin_ppm']
            self.axis_pars['end_ppm'] = self.info['plot_end_ppm'] - width*self.rang[0]
            self.axis_pars['begin_ppm'] = self.info['plot_begin_ppm'] + width*(1-self.rang[1])
            self.zoom_button.setChecked(False)
            self.update()
            self.zooming = False

        if self.integrating:
            print(absrang) #spectrum should get this absrang and come up with integration output
            self.integrate_button.setChecked(False)
            self.integrating = False

    def paintEvent(self, event):

        # settings
        painter = QPainter(self)

        # updating window size
        rect = self.rect()
        self.p_size = {
            'w': rect.topRight().x()-rect.topLeft().x(),
            'h': rect.bottomLeft().y()-rect.topRight().y()
        }
        if not self.drawstatus:
            message = 'nothing loaded'
            font_metrics = QFontMetrics(self.font())
            text_width = font_metrics.horizontalAdvance(message)
            painter.drawText(
                QPointF(self.p_size['w']/2 - text_width, self.p_size['h']/2), message)
            return None

        painter.setFont(self.textfont)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

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


class openNMR(QMainWindow):
    def __init__(self):
        super().__init__()
        # open folder
        button_layout = QHBoxLayout()
        self.file_button = QPushButton("Open Folder")
        self.file_button.clicked.connect(self.openFile)
        button_layout.addWidget(self.file_button)

        # zoom button
        self.zoom_button = QPushButton("Zoom")
        self.zoom_button.setCheckable(True)
        self.zoom_button.toggled.connect(self.toggle_dragging)

        # reset zoom button
        self.zoom_reset_button = QPushButton("Reset Zoom")
        self.zoom_reset_button.clicked.connect(self.reset_zoom)

        self.integrate_button = QPushButton("Integrate Manually")
        self.integrate_button.setCheckable(True)
        self.integrate_button.clicked.connect(self.toggle_integration)

        # to implement
        button_layout.addWidget(self.zoom_button)
        button_layout.addWidget(self.zoom_reset_button)
        button_layout.addWidget(self.integrate_button)
        button_layout.addWidget(QPushButton("Find Peaks"))

        # widnow size, position, margins, etc
        size = {'w': 800, 'h': 400}
        self.setGeometry(200, 200, size['w'], size['h'])

        # opening spectrum, in the future on event
        self.experiments = []

        # modifying in relation to spectrum
        self.painter_widget = spectrum_painter(
            self.zoom_button, self.integrate_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.painter_widget)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def toggle_dragging(self, checked):
        self.painter_widget.zooming = True

    def toggle_integration(self, checked):
        self.painter_widget.integrating = True

    def reset_zoom(self):
        self.painter_widget.rang = [0, 1]
        self.painter_widget.startPos = 0
        self.painter_widget.endPos = 1
        self.painter_widget.axis_pars['begin_ppm'] = self.painter_widget.info['plot_begin_ppm']
        self.painter_widget.axis_pars['end_ppm'] = self.painter_widget.info['plot_end_ppm']
        self.painter_widget.update()

    def openFile(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle('Choose a folder')
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        selected_file = []
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            title = "Open NMR"
            self.painter_widget.generate_data(
                Spectrum_1D.create_from_file(selected_file))
            title += ' - ' + selected_file
            self.setWindowTitle(title)
        self.painter_widget.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    QFontDatabase.addApplicationFont("styling/titillium.ttf")
    with open("styling/styles.qss", "r") as f:
        style = f.read()
        app.setStyleSheet(style)
    # main app
    window = openNMR()
    window.show()
    sys.exit(app.exec())
