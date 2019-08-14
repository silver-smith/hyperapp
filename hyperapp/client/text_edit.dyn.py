import logging

from PySide import QtCore, QtGui

from hyperapp.client.object import ObjectObserver
from hyperapp.client.module import ClientModule
from . import htypes
from .text_object import TextObject
from .layout_registry import LayoutViewProducer

_log = logging.getLogger(__name__)


class TextEditView(QtGui.QTextEdit, ObjectObserver):

    def __init__(self, object):
        super().__init__()
        self.object = object
        self.notify_on_text_changed = True
        self.setPlainText(object.text)
        self.textChanged.connect(self._on_text_changed)
        self.object.subscribe(self)

    def get_title(self):
        return self.object.get_title()

    def _on_text_changed(self):
        if self.notify_on_text_changed:
            self.object.text_changed(self.toPlainText(), emitter_view=self)

    # todo: preserve cursor position
    def object_changed(self):
        self.notify_on_text_changed = False
        try:
            self.setPlainText(self.object.text)
        finally:
            self.notify_on_text_changed = True
        View.object_changed(self)

    def __del__(self):
        _log.info('~text_edit %r', self)


class TextEditProducer(LayoutViewProducer):

    def __init__(self, layout):
        pass

    async def produce_view(self, type_ref, object, observer=None):
        return TextEditView(object)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.layout_registry.register_type(htypes.text.text_edit_layout, TextEditProducer)
