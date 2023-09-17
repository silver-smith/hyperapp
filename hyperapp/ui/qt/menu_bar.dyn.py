from PySide6 import QtWidgets


class MenuBarCtl:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def __init__(self):
        pass

    def construct_widget(self, state, ctx):
        w = QtWidgets.QMenuBar()
        menu = QtWidgets.QMenu('&All')
        w.addMenu(menu)
        return w
