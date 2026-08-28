from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget


class Spinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.angle = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)

        self.setFixedSize(48, 48)

    def start(self):
        self.timer.start(50)

    def stop(self):
        self.timer.stop()

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = self.rect().center()

        painter.translate(center)
        painter.rotate(self.angle)

        for index in range(12):
            opacity = (index + 1) / 12

            color = Qt.GlobalColor.gray
            pen = QPen(color)
            pen.setWidth(4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)

            color = pen.color()
            color.setAlphaF(opacity)
            pen.setColor(color)

            painter.setPen(pen)

            painter.drawLine(0, -16, 0, -22)
            painter.rotate(30)


class ProcessingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            ProcessingOverlay {
                background-color: white;
            }
        """)

        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
            True
        )

        self.setStyleSheet("""
            ProcessingOverlay {
                background-color: rgba(255, 255, 255, 220);
            }
        """)

        self.spinner = Spinner(self)

        self.hide()

    def start(self):
        self.show()
        self.raise_()

        self.spinner.move(
            (self.width() - self.spinner.width()) // 2,
            (self.height() - self.spinner.height()) // 2
        )

        self.spinner.start()

    def stop(self):
        self.spinner.stop()
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.spinner.move(
            (self.width() - self.spinner.width()) // 2,
            (self.height() - self.spinner.height()) // 2
        )