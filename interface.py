import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QStackedWidget, QLabel, QFrame
from PyQt6.QtGui import QPainter, QPolygonF, QFontMetrics, QFont, QFontDatabase, QPen, QColor
from PyQt6.QtCore import QPointF, Qt
import numpy as np
from spectrum import Spectrum_1D
import math


def axis_generator(painter, p_size, axis_pars, textfont):
    # drawing axis delimiters, adjusts automatically
    # parameters
    ax_pos = p_size['h']-axis_pars['ax_padding']
    width = axis_pars['end_ppm']-axis_pars['begin_ppm']
    incr_ppm = 2**round(np.log2(width *
                        axis_pars['pixperinc']/math.ceil(p_size['w'])))
    incr_fac = incr_ppm/width
    # axis line
    painter.drawLine(QPointF(0.0, ax_pos),
                     QPointF(p_size['w'], ax_pos))
    # increments lists
    del_pos_list = []
    if axis_pars['end_ppm'] > 0 and axis_pars['begin_ppm'] < 0:
        iterright = math.ceil(axis_pars['end_ppm']/incr_ppm)
        iterleft = math.ceil(abs(axis_pars['begin_ppm']/incr_ppm))
        del_pos_list = [axis_pars['end_ppm']/width -
                        i*incr_fac for i in range(iterright)]
        negative_list = [axis_pars['end_ppm']/width +
                         i*incr_fac for i in range(iterleft)]
        del_pos_list.extend(negative_list)
    else:
        del_pos_list = [axis_pars['end_ppm'] % incr_ppm/width +
                        i*incr_fac for i in range(math.ceil(width/incr_ppm))]
    del_pos_list = list(set(del_pos_list))
    del_pos_list = [i for i in del_pos_list if i >
                    0+20/p_size['w'] and i < 1-20/p_size['w']]
    del_text_list = [str(round(axis_pars['end_ppm']-i*width, 3))
                     for i in del_pos_list]

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
        if sample < 4:
            return data
        for pix in range(int(math.ceil(len(data)/sample))):
            start = pix*sample
            end = min((pix+1)*sample-1, len(data)-1)
            if start == end:
                resampled.append(data[-1])
                break
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
        self.pen = QPen(QColor("black"))
        self.rang = [0, 1]
        # dragging
        self.zooming = False
        self.integrating = False
        self.startPos = 0
        self.endPos = 1

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
            # spectrum should get this absrang and come up with integration output
            print(absrang)
            self.integrate_button.setChecked(False)
            self.integrating = False

    def paintEvent(self, event):
        # settings
        painter = QPainter(self)
        painter.setPen(self.pen)
        # updating window size
        rect = self.rect()
        self.p_size = {
            'w': rect.topRight().x()-rect.topLeft().x(),
            'h': rect.bottomLeft().y()-rect.topRight().y()
        }
        if not self.drawstatus:
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

class tab_button(QFrame):
    def __init__(self):
        super().__init__()


class openNMR(QMainWindow):
    def __init__(self):
        super().__init__()
        title = "Open NMR"
        self.setWindowTitle(title)

        self.file_button = QPushButton("Open Folder")
        self.file_button.clicked.connect(self.openFile)

        self.zoom_button = QPushButton("Zoom")
        self.zoom_button.setCheckable(True)
        self.zoom_button.toggled.connect(self.toggle_dragging)

        self.zoom_reset_button = QPushButton("Reset Zoom")
        self.zoom_reset_button.clicked.connect(self.reset_zoom)

        self.integrate_button = QPushButton("Integrate Manually")
        self.integrate_button.setCheckable(True)
        self.integrate_button.clicked.connect(self.toggle_integration)

        actions_frame = QFrame()
        actions = QVBoxLayout(actions_frame)
        actions.addWidget(QLabel('Actions'))
        actions.addWidget(self.file_button)
        actions.addWidget(self.zoom_button)
        actions.addWidget(self.zoom_reset_button)
        actions.addWidget(self.integrate_button)
        actions.addWidget(QPushButton("Find Peaks"))
        actions.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        tabs_frame = QFrame()
        self.tabs = QVBoxLayout(tabs_frame)
        self.tabs.addWidget(QLabel('Tabs'))
        self.tabs.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        
        toolbar = QVBoxLayout()
        toolbar.addWidget(actions_frame)
        toolbar.addWidget(tabs_frame)
        

        # widnow size, position, margins, etc
        size = {'w': 800, 'h': 400}
        self.setGeometry(200, 200, size['w'], size['h'])

        # modifying in relation to spectrum
        self.spectrum_viewer = QStackedWidget()
        self.spectrum_viewer.setObjectName('spectrumviewer')

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.spectrum_viewer)
        main_layout.addLayout(toolbar)
        
        complete_window = QWidget()
        complete_window.setLayout(main_layout)
        self.setCentralWidget(complete_window)

    def toggle_dragging(self, checked):
        current = self.spectrum_viewer.currentWidget()
        if current:
            current.zooming = True

    def toggle_integration(self, checked):
        current = self.spectrum_viewer.currentWidget()
        if current:
            current.integrating = True

    def reset_zoom(self):
        current = self.spectrum_viewer.currentWidget()
        if current:
            current.rang = [0, 1]
            current.startPos = 0
            current.endPos = 1
            current.axis_pars['begin_ppm'] = current.info['plot_begin_ppm']
            current.axis_pars['end_ppm'] = current.info['plot_end_ppm']
            current.update()

    def openFile(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle('Choose a folder')
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        selected_file = []
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.add_new_page(selected_file)

    def add_new_page(self, file):
        page_index = round(self.spectrum_viewer.count())
        painter_widget = spectrum_painter(
            self.zoom_button, self.integrate_button)
        painter_widget.generate_data(Spectrum_1D.create_from_file(file))
        self.spectrum_viewer.addWidget(painter_widget)
        button = QPushButton(painter_widget.info['samplename'])
        button.clicked.connect(lambda: self.spectrum_viewer.setCurrentIndex(page_index))
        self.tabs.addWidget(button)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle('Fusion')
    QFontDatabase.addApplicationFont("styling/titillium.ttf")
    with open("styling/styles.css", "r") as f:
        style = f.read()
        app.setStyleSheet(style)
    # main app
    window = openNMR()
    window.show()
    sys.exit(app.exec())
