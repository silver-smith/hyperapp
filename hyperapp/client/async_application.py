# qt application with async loop support

import asyncio
import logging
import traceback

from qasync import QEventLoop
from PySide2 import QtCore, QtWidgets

_log = logging.getLogger(__name__)


class AsyncApplication(QtWidgets.QApplication):

    def __init__(self, sys_argv=None):
        super().__init__(sys_argv or [])
        self.event_loop = QEventLoop(self)
        self.event_loop.set_debug(True)
        # self.event_loop.set_exception_handler(self._async_exception_handler)
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

    def _async_exception_handler(self, loop, context):
        exception = context['exception']
        exception_tb = traceback.format_exception(exception.__class__, exception, exception.__traceback__)
        source_tb = traceback.StackSummary.from_list(context['source_traceback']).format()
        _log.error("%s\n%s\nSource traceback:\n%s", context['message'], ''.join(exception_tb), ''.join(source_tb))
