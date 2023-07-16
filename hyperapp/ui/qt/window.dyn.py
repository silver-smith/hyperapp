from PySide6 import QtWidgets

from . import htypes


DUP_OFFSET = htypes.window.pos(150, 50)


class WindowCtl:

    def __init__(self, piece):
        super().__init__()

    def construct_widget(self, ctx):
        w = QtWidgets.QMainWindow()
        w.setCentralWidget(QtWidgets.QLabel("Hello!"))
        return w

    def duplicate(self, widget):
        pass
