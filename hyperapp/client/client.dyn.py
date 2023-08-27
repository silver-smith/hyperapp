from PySide6 import QtWidgets

from .services import (
    ui_ctl_creg,
    )


def _main():
    app = QtWidgets.QApplication()

    window = QtWidgets.QMainWindow()
    window.resize(1000, 800)
    window.move(500, 100)
    window.show()

    window.setCentralWidget(QtWidgets.QLabel("Hello!"))

    return app.exec()
