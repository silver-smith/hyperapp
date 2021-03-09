import asyncio
import logging

from qasync import QEventLoop
from PySide2 import QtWidgets

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.event_loop_ctr = self.event_loop_ctr
        services.event_loop_dtr = self.event_loop_dtr

    def event_loop_ctr(self):
        log.info("Construct Qt event loop")
        self._app = QtWidgets.QApplication()
        return QEventLoop(self._app)

    def event_loop_dtr(self):
        self._app.shutdown()
