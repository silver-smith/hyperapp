from PySide6 import QtWidgets

from .code.mark import mark


@mark.fixture
def qapp():
    app = QtWidgets.QApplication()
    yield app
    app.shutdown()
