import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QStackedWidget, QLabel, QFrame, QGridLayout
from PyQt5.QtGui import QPainter, QPolygonF, QFontMetrics, QFont, QFontDatabase, QPen, QColor, QBrush
from PyQt5.QtCore import QPointF, Qt
import numpy as np
from spectrum import Spectrum_1D
import math
from helper import *

class spectrum_painter(QWidget):
    def __init__(self, zoom_button, integrate_button, remove_button, pick_peak, palette2):
        super().__init__()
        self.zoom_button = zoom_button
        self.integrate_button = integrate_button
        self.remove_button = remove_button
        self.pick_peak = pick_peak
        self.drawstatus = False
        self.textfont = QFont('Times New Roman', 10)
        self.pen = QPen(QColor("black"))
        self.palette2 = palette2
        self.width_vis = [0, 1]
        self.int_rangs = []
        # dragging
        self.current_action = None
        self.sel_region = [[0,0], [0,0]]
        self.selectstart = None
        self.selectend = None
        self.range_actions = ['integrating','zooming','pickpeak']
        self.box_actions = ['removing']

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
        del_pos_list = [i for i in del_pos_list if i > 20/self.p_size['w'] and i < 1-20/self.p_size['w']]
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
                          'incperppm': 100,
                          'ax_padding': 30,
                          'spect_top_padding': 70,
                          'spect_bottom_padding': 100,
                          'end_ppm': self.info['plot_end_ppm'],
                          'begin_ppm': self.info['plot_begin_ppm']}
        self.artist_pars = {'integ_pos':20, 'integ_sep':5, 'br_width':2, 'peak_pos':20, 'peak_sep':5}
        # deln is a length of delimiter in pixels
        # incperppm: multiples - 2 => 0.5 is the minimum increment

    def mousePressEvent(self, event):
        self.selectstart = event.pos()
        if self.current_action:
            self.sel_region[0][0] = self.selectstart.x()/self.p_size['w']

    def mouseMoveEvent(self, event):
        self.selectend = event.pos()
        if self.current_action:
            self.sel_region[1][0] = self.selectend.x()/self.p_size['w']
            self.update()

    def mouseReleaseEvent(self, event):
        # adjusting rang
        width_select = [self.sel_region[0][0], self.sel_region[1][0]]
        width_select.sort()
        width_select_abs = [self.width_vis[0]+(self.width_vis[1]-self.width_vis[0])*width_select[0],
                   self.width_vis[0]+(self.width_vis[1]-self.width_vis[0])*width_select[1]
                   ]
        width_select_abs.sort()
        
        if self.current_action=='zooming':
            self.width_vis = width_select_abs
            # adjusting axis
            width = self.info['plot_end_ppm']-self.info['plot_begin_ppm']
            self.axis_pars['end_ppm'] = self.info['plot_end_ppm'] - width*self.width_vis[0]
            self.axis_pars['begin_ppm'] = self.info['plot_begin_ppm'] + width*(1-self.width_vis[1])
            

        if self.current_action=='integrating':
            self.experiment.integrate(width_select_abs[0], width_select_abs[1], vtype="fraction")
        
        if self.current_action=='removing':
            self.experiment.integral_list = [el for el in self.experiment.integral_list if el[0]>width_select_abs[1] or el[1]<width_select_abs[0]]
        
        if self.current_action=='pickpeak':self.experiment.quick_peak(width_select_abs)

        self.update()
        self.integrate_button.setChecked(False)
        self.zoom_button.setChecked(False)
        self.remove_button.setChecked(False)
        self.pick_peak.setChecked(False)
        self.current_action = None
        self.selectend = None
        self.selectstart = None

    def paintEvent(self, event):
        painter = QPainter(self)
        
        #when selecting
        accent = self.palette2['accent']
        accent.setAlphaF(0.5)
        painter.setPen(QPen(accent, 0, Qt.SolidLine))
        painter.setBrush(QBrush(accent))
        if any([state==self.current_action for state in self.range_actions]):
            painter.drawRect(self.selectstart.x(), 0,
                             self.selectend.x() - self.selectstart.x(),
                             self.p_size['h'])

        if any([state==self.current_action for state in self.box_actions]):
            painter.drawRect(self.selectstart.x(), self.selectstart.y(),
                             self.selectend.x() - self.selectstart.x(),
                             self.selectend.y() - self.selectstart.y())

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
                                   self.p_size['h'] - self.axis_pars['spect_top_padding'] - self.axis_pars['spect_bottom_padding'],
                                   self.width_vis)
        self.resampled = [QPointF(i[0], i[1]+self.axis_pars['spect_bottom_padding']) for i in self.resampled]
        painter.drawPolyline(QPolygonF(self.resampled))
    
        self.axis_generator(painter)
        self.integration_marks(painter)
        self.peak_marks(painter)
        painter.end()

    def integration_marks(self, painter):
        label_padding = self.p_size['h']-self.axis_pars['spect_top_padding']+self.artist_pars['integ_pos']
        bracket_padding = self.p_size['h']-self.axis_pars['spect_top_padding']+self.artist_pars['integ_sep']
        label_list = []
        painter.setPen(QPen(self.palette2['accent-dark']))
        for i in range(len(self.experiment.integral_list)):
            integ = self.experiment.integral_list[i]
            begin, end, real_value, relative_value = integ
            if end > self.width_vis[1] or begin < self.width_vis[0]: continue

            # correction for zoomed view
            rightend = (end-self.width_vis[0])/(self.width_vis[1]-self.width_vis[0])
            leftend = (begin-self.width_vis[0])/(self.width_vis[1]-self.width_vis[0])
            labl_pos = (rightend+leftend)/2
            
            # the label itself, drawn in next loop
            integ_name = str(round(relative_value,2))
            font_metrics = QFontMetrics(self.textfont)
            text_width = font_metrics.horizontalAdvance(integ_name)
            num_pos = labl_pos*self.p_size['w']-0.5*text_width
            label_list.append([num_pos, text_width, integ_name])
            
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
        label_list = rearrange(label_list)
        painter.setPen(self.pen)
        for label in label_list:
            painter.drawText(QPointF(label[0], label_padding), label[2])
        pass

    def peak_marks(self, painter):
        label_padding = self.artist_pars['peak_pos']
        label_sep = self.artist_pars['peak_pos']+self.artist_pars['peak_sep']
        label_list = []
        for i in range(len(self.experiment.peak_list)):
            peak = self.experiment.peak_list[i]
            if peak[0]>self.width_vis[1] or peak[0]<self.width_vis[0]: continue
            peak_pos = (peak[0]-self.width_vis[0])/(self.width_vis[1]-self.width_vis[0])
            peak_name = str(round(peak[1],2))
            font_metrics = QFontMetrics(self.textfont)
            text_width = font_metrics.horizontalAdvance(peak_name)
            peak_pos = peak_pos*self.p_size['w']-0.5*text_width
            label_list.append([peak_pos, text_width, peak_name])
        
        label_list = rearrange(label_list)
        painter.setPen(self.pen)
        for peak_name in label_list:
            painter.drawText(QPointF(peak_name[0], label_padding), peak_name[2])


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
        self.additional_palette = {'accent' : QColor("#558B6E"),
                                   'accent-dark': QColor("#3B614D")}

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

        self.remove_buton = QPushButton("Remove Element")
        self.remove_buton.setCheckable(True)
        self.remove_buton.clicked.connect(self.toggle_removing)

        self.pick_peak = QPushButton("Pick Peak")
        self.pick_peak.setCheckable(True)
        self.pick_peak.clicked.connect(self.toggle_peaks)

        actions_frame = QFrame()
        actions = QVBoxLayout(actions_frame)
        actions.addWidget(QLabel('Viewing'))
        actions.addWidget(self.file_button)
        actions.addWidget(self.zoom_button)
        actions.addWidget(self.zoom_reset_button)
        actions.addWidget(QLabel('Editing'))
        actions.addWidget(self.integrate_button)
        actions.addWidget(self.remove_buton)
        actions.addWidget(self.pick_peak)
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
            current.current_action = 'zooming'

    def toggle_integration(self, checked):
        current = self.spectrum_viewer.currentWidget()
        if current:
            current.current_action = 'integrating'
    
    def toggle_removing(self, checked):
        current = self.spectrum_viewer.currentWidget()
        if current:
            current.current_action = 'removing'

    def toggle_peaks(self, checked):
        current = self.spectrum_viewer.currentWidget()
        if current:
            current.current_action = 'pickpeak'

    def reset_zoom(self):
        current = self.spectrum_viewer.currentWidget()
        if current:
            current.width_vis = [0, 1]
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
            self.zoom_button, self.integrate_button, self.remove_buton, self.pick_peak, self.additional_palette)
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
