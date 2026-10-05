from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QPaintEvent, QResizeEvent
from PySide6.QtWidgets import QWidget


class Spinner(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.angle = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)

        self.setFixedSize(48, 48)

    def start(self) -> None:
        self.timer.start(50)

    def stop(self) -> None:
        self.timer.stop()

    def rotate(self) -> None:
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
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

            pen_color = pen.color()
            pen_color.setAlphaF(opacity)
            pen.setColor(pen_color)

            painter.setPen(pen)

            painter.drawLine(0, -16, 0, -22)
            painter.rotate(30)


class ProcessingOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
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

    def start(self) -> None:
        self.show()
        self.raise_()

        self.spinner.move(
            (self.width() - self.spinner.width()) // 2,
            (self.height() - self.spinner.height()) // 2
        )

        self.spinner.start()

    def stop(self) -> None:
        self.spinner.stop()
        self.hide()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        self.spinner.move(
            (self.width() - self.spinner.width()) // 2,
            (self.height() - self.spinner.height()) // 2
        )