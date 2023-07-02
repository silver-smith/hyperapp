from PySide6 import QtWidgets

from . import htypes


DUP_OFFSET = htypes.window.pos(150, 50)


class Window(QtWidgets.QMainWindow):

    def __init__(self, piece):
        super().__init__()
        self.setCentralWidget(QtWidgets.QLabel("Hello!"))

    def duplicate(self):
        pass
