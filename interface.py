import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QStackedWidget, QLabel, QFrame, QGridLayout
from PyQt5.QtGui import QPainter, QPolygonF, QFontMetrics, QFont, QFontDatabase, QPen, QColor, QBrush, QPalette
from PyQt5.QtCore import QPointF, Qt
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

def rearrange(boxlis):
    """
    rearranges boxlike (position,width) entities on a scale of 0,1 so that they don't overlap
    fast, unrealiable, cheap and cumbersome, also known as fucc
    """
    print([i[0] for i in boxlis])
    for n in range(20):
        tempboxlis = boxlis.copy()
        for i in range(len(boxlis)):
            for j in range(len(boxlis)):
                if i==j:continue
                diff = boxlis[i][0]-boxlis[j][0]
                if abs(diff)<1.1*(boxlis[i][1]/2+boxlis[j][1]/2):
                    tempboxlis[i][0] += 0.1*np.sign(diff)*abs(diff)
        boxlis = tempboxlis
    print([i[0] for i in boxlis])
    return boxlis

class spectrum_painter(QWidget):
    def __init__(self, zoom_button, integrate_button, palette2):
        super().__init__()
        self.zoom_button = zoom_button
        self.integrate_button = integrate_button
        self.drawstatus = False
        self.textfont = QFont('Times New Roman', 10)
        self.pen = QPen(QColor("black"))
        self.palette2 = palette2
        self.rang = [0, 1]
        self.int_rangs = []
        # dragging
        self.zooming = False
        self.integrating = False
        self.startPos = 0
        self.endPos = 1
        self.selectstart = None
        self.selectend = None

    def axis_generator(self, painter):
        # drawing axis delimiters, adjusts automatically
        # parameters
        ax_pos = self.p_size['h']-self.axis_pars['ax_padding']
        width = self.axis_pars['end_ppm']-self.axis_pars['begin_ppm']
        incr_ppm = 2**round(np.log2(width *
                            self.axis_pars['pixperinc']/math.ceil(self.p_size['w'])))
        incr_fac = incr_ppm/width
        # axis line
        painter.drawLine(QPointF(0.0, ax_pos),
                        QPointF(self.p_size['w'], ax_pos))
        # increments lists
        del_pos_list = []
        if self.axis_pars['end_ppm'] > 0 and self.axis_pars['begin_ppm'] < 0:
            iterright = math.ceil(self.axis_pars['end_ppm']/incr_ppm)
            iterleft = math.ceil(abs(self.axis_pars['begin_ppm']/incr_ppm))
            del_pos_list = [self.axis_pars['end_ppm']/width -
                            i*incr_fac for i in range(iterright)]
            negative_list = [self.axis_pars['end_ppm']/width +
                            i*incr_fac for i in range(iterleft)]
            del_pos_list.extend(negative_list)
        else:
            del_pos_list = [self.axis_pars['end_ppm'] % incr_ppm/width +
                            i*incr_fac for i in range(math.ceil(width/incr_ppm))]
        del_pos_list = list(set(del_pos_list))
        del_pos_list = [i for i in del_pos_list if i >
                        0+20/self.p_size['w'] and i < 1-20/self.p_size['w']]
        del_text_list = [str(round(self.axis_pars['end_ppm']-i*width, 3))
                        for i in del_pos_list]

        # draw delimiters
        for i in range(len(del_pos_list)):
            del_pos = del_pos_list[i]
            del_text = del_text_list[i]
            top_del = QPointF(
                del_pos*self.p_size['w'], ax_pos+self.axis_pars['dlen'])
            bot_del = QPointF(
                del_pos*self.p_size['w'], ax_pos-self.axis_pars['dlen'])
            painter.drawLine(top_del, bot_del)
            # paramters for text
            font_metrics = QFontMetrics(self.textfont)
            text_width = font_metrics.horizontalAdvance(del_text)
            num_pos = QPointF(
                del_pos*self.p_size['w']-0.5*text_width, ax_pos+4*self.axis_pars['dlen'])
            painter.drawText(num_pos, del_text)

    def data_and_pars(self, experiment):
        # data
        self.drawstatus = True
        self.experiment = experiment
        self.data = experiment.spectrum.copy()
        self.info = experiment.info.copy()
        self.resampled = []
        self.axis_pars = {'dlen': 5, 'pixperinc': 70,
                          'incperppm': 100, 'ax_padding': 30, 'spect_padding': 70,
                          'end_ppm': self.info['plot_end_ppm'],
                          'begin_ppm': self.info['plot_begin_ppm']}
        self.artist_pars = {'marksep':20, 'bracketsep':5, 'br_width':2}
        # deln is a length of delimiter in pixels
        # incperppm: multiples - 2 => 0.5 is the minimum increment

    def mousePressEvent(self, event):
        self.selectstart = event.pos()
        if self.zooming or self.integrating:
            self.startPos = self.selectstart.x()/self.p_size['w']

    def mouseMoveEvent(self, event):
        self.selectend = event.pos()
        if self.zooming or self.integrating:
            self.endPos = self.selectend.x()/self.p_size['w']
            self.update()

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
            self.experiment.integrate(absrang[0], absrang[1], vtype="fraction")
            self.integrate_button.setChecked(False)
            self.integrating = False
            self.update()
        self.selectend = None
        self.selectstart = None

    def paintEvent(self, event):
        painter = QPainter(self)
        
        #when selecting
        accent = self.palette2['accent']
        accent.setAlphaF(0.5)
        painter.setPen(QPen(accent, 0, Qt.SolidLine))
        painter.setBrush(QBrush(accent))
        if self.selectstart and self.selectend:
            painter.drawRect(self.selectstart.x(), 0,
                             self.selectend.x() - self.selectstart.x(),
                             self.p_size['h'])

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
        self.axis_generator(painter)
        self.integration_marks(painter)
        painter.end()

    def integration_marks(self, painter):
        mark_padding = self.p_size['h']-self.axis_pars['spect_padding']+self.artist_pars['marksep']
        bracket_padding = self.p_size['h']-self.axis_pars['spect_padding']+self.artist_pars['bracketsep']
        marklist = []
        for integ in self.experiment.integral_list:
            if integ[5] > self.rang[1] or integ[4] < self.rang[0]: continue

            # correction for zoomed view
            rightend = (integ[5]-self.rang[0])/(self.rang[1]-self.rang[0])
            leftend = (integ[4]-self.rang[0])/(self.rang[1]-self.rang[0])
            mark_pos = (rightend+leftend)/2
            
            # the mark itself, drawn in next loop
            integ_name = str(round(integ[3],2))
            font_metrics = QFontMetrics(self.textfont)
            text_width = font_metrics.horizontalAdvance(integ_name)
            num_pos = mark_pos*self.p_size['w']-0.5*text_width
            marklist.append([num_pos, text_width, integ_name])
            
            # the bracket
            painter.drawLine(
                QPointF(rightend*self.p_size['w'], bracket_padding),
                QPointF(leftend*self.p_size['w'], bracket_padding)
                )
            painter.drawLine(
                QPointF(rightend*self.p_size['w'], bracket_padding-self.artist_pars['br_width']),
                QPointF(rightend*self.p_size['w'], bracket_padding+self.artist_pars['br_width'])
                )
            painter.drawLine(
                QPointF(leftend*self.p_size['w'], bracket_padding-self.artist_pars['br_width']),
                QPointF(leftend*self.p_size['w'], bracket_padding+self.artist_pars['br_width'])
                )
        marklist = rearrange(marklist)
        for mark in marklist:
            painter.drawText(QPointF(mark[0], mark_padding), mark[2])
        pass

class TabFrameWidget(QFrame):
    def __init__(self, sv_w):
        super().__init__()
        self.setObjectName('tabframe')
        self.sv_w = sv_w
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel('Tabs'))
        
        self.buttongrid = QGridLayout()
        layout.addLayout(self.buttongrid)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.buttongrid.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.pt_indexlis = []
    
    def add_tab(self, pt_w):
        sele_btn = QPushButton(pt_w.info['samplename'])
        sele_btn.setObjectName('selebtn')
        sele_btn.clicked.connect(self.seleClicked)
        close_btn = QPushButton('-')
        close_btn.setObjectName('closebtn')
        close_btn.clicked.connect(self.deleClicked)
        num = self.buttongrid.rowCount()
        self.buttongrid.setHorizontalSpacing(0)
        self.buttongrid.addWidget(sele_btn, num, 0)
        self.buttongrid.addWidget(close_btn, num, 1)
        pt_index = 0
        if self.pt_indexlis: pt_index += self.pt_indexlis[-1][1]+1
        self.pt_indexlis.append([pt_w.info['samplename'], pt_index, pt_w])
    
    def seleClicked(self):
        sender = self.sender()
        if sender:
            index = [t for t in self.pt_indexlis if t[0]==sender.text()][0][1]
            self.sv_w.setCurrentIndex(index)
    
    def deleClicked(self):
        sender = self.sender()
        if sender:
            bt_index = self.buttongrid.getItemPosition(self.buttongrid.indexOf(sender))[0]
            self.buttongrid.itemAtPosition(bt_index, 1).widget().deleteLater()
            selew = self.buttongrid.itemAtPosition(bt_index, 0).widget()
            selew.deleteLater()
            pt_index = [t for t in self.pt_indexlis if t[0]==selew.text()][0][1]
            self.pt_indexlis[pt_index][2].deleteLater()
            self.pt_indexlis.pop(pt_index)
            for i in range(len(self.pt_indexlis)):
                self.pt_indexlis[i][1] = i

class openNMR(QMainWindow):
    def __init__(self):
        super().__init__()
        self.additional_palette = {}
        self.additional_palette['accent'] = QColor("#558B6E")

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
        
        self.spectrum_viewer = QStackedWidget()
        self.spectrum_viewer.setObjectName('spectrumviewer')

        self.tabs_frame = TabFrameWidget(self.spectrum_viewer)
        
        toolbar = QVBoxLayout()
        toolbar.addWidget(actions_frame)
        toolbar.addWidget(self.tabs_frame)

        # widnow size, position, margins, etc
        size = {'w': 800, 'h': 400}
        self.setGeometry(200, 200, size['w'], size['h'])

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.spectrum_viewer)
        main_layout.addLayout(toolbar)
        
        complete_window = QWidget()
        complete_window.setLayout(main_layout)
        self.setCentralWidget(complete_window)

        if sys.argv:
            for filename in sys.argv:
                if filename.endswith('.fid/'):
                    try: self.add_new_page(filename)
                    except: pass

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
            self.zoom_button, self.integrate_button, self.additional_palette)
        painter_widget.data_and_pars(Spectrum_1D.create_from_file(file))
        
        self.spectrum_viewer.addWidget(painter_widget)
        self.tabs_frame.add_tab(painter_widget)


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
