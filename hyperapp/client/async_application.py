# qt application with async loop support

import asyncio
from PySide import QtCore, QtGui


class AsyncApplication(QtGui.QApplication):

    def __init__(self, sys_argv=None):
        QtGui.QApplication.__init__(self, sys_argv or [])
        self.event_loop = asyncio.get_event_loop()
        self.event_loop.set_debug(True)

    def stop_loop(self):
        asyncio.async(self._stop_loop_async())  # call it async to allow all pending tasks to complete

    @asyncio.coroutine
    def _stop_loop_async(self):
        self.event_loop.stop()

    # process qt events while inside asyncio loop
    def _process_events_and_repeat(self):
        while self.hasPendingEvents():
            self.processEvents()
            # although this event is documented as deprecated, it is essential for qt objects being destroyed:
            self.processEvents(QtCore.QEventLoop.DeferredDeletion)
        self.sendPostedEvents(None, 0)
        self.event_loop.call_later(0.01, self._process_events_and_repeat)

    def exec_(self):
        self.event_loop.call_soon(self._process_events_and_repeat)
        try:
            self.event_loop.run_forever()
        finally:
            self.event_loop.close()
