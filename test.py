import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt


class RectangleWidget(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.SolidLine)
        painter.setBrush(QColor(255, 0, 0))
        rect = self.rect()
        painter.drawRect(rect)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Resizable Rectangle")
        self.setGeometry(100, 100, 500, 400)

        self.rect_widget = RectangleWidget()
        self.setCentralWidget(self.rect_widget)

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())