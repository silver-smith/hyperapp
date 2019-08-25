# qt application with async loop support

import asyncio

from asyncqt import QEventLoop
from PySide2 import QtCore, QtWidgets


class AsyncApplication(QtWidgets.QApplication):

    def __init__(self, sys_argv=None):
        super().__init__(sys_argv or [])
        self.event_loop = QEventLoop(self)
        self.event_loop.set_debug(True)
        asyncio.set_event_loop(self.event_loop)

    def stop_loop(self):
        asyncio.ensure_future(self._stop_loop_async())  # call it async to allow all pending tasks to complete

    async def _stop_loop_async(self):
        self.event_loop.stop()

    def run_event_loop(self):
        try:
            self.event_loop.run_forever()
        finally:
            self.event_loop.close()
