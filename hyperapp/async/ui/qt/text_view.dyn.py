import logging
import asyncio
import re

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes
from .object import ObjectObserver
from .view import View
from .string_object import StringObject

log = logging.getLogger(__name__)


class TextView(View, QtWidgets.QTextBrowser):

    @classmethod
    async def from_piece(cls, piece, object, add_dir_list):
        return cls(object)

    def __init__(self, object):
        QtWidgets.QTextBrowser.__init__(self)
        View.__init__(self)
        self.setOpenLinks(False)
        # self._view_opener = view_opener
        self._object = object
        self.setHtml(self.text2html(object.value or ''))
        self.anchorClicked.connect(self.on_anchor_clicked)
        self.object.subscribe(self)

    @property
    def piece(self):
        return htypes.text_view.text_view()

    @property
    def object(self):
        return self._object

    @property
    def state(self):
        return None

    @property
    def title(self):
        return self.object.title

    def text2html(self, text):
        return re.sub(r'\[([^\]]+)\]', r'<a href="\1">\1</a>', text or '')

    def on_anchor_clicked(self, url):
        log.info('on_anchor_clicked url.path=%r', url.path())
        asyncio.ensure_future(self.open_url(url))

    async def open_url(self, url):
        pass
        # rec = await self.object.open_ref(url.path())
        # todo: pass this piece to navigator to open
        # if rec is not None:
        #     await self._view_opener.open_rec(rec)

    def object_changed(self):
        self.setHtml(self.text2html(self.object.text))
        View.object_changed(self)

    # def __del__(self):
    #     log.info('~text_view %r', self)


class TextEditView(View, QtWidgets.QTextEdit, ObjectObserver):

    @classmethod
    async def from_piece(cls, piece, object):
        return cls(object)

    def __init__(self, object):
        QtWidgets.QTextEdit.__init__(self)
        View.__init__(self)
        ObjectObserver.__init__(self)
        self._object = object
        self.notify_on_text_changed = True
        self.setPlainText(object.value)
        self.textChanged.connect(self._on_text_changed)
        self._object.subscribe(self)

    @property
    def piece(self):
        return htypes.text_view.text_view()

    @property
    def object(self):
        return self._object

    @property
    def state(self):
        return None

    @property
    def title(self):
        return self._object.title

    def _on_text_changed(self):
        if self.notify_on_text_changed:
            self._object.text_changed(self.toPlainText(), emitter_view=self)

    # todo: preserve cursor position
    def object_changed(self):
        self.notify_on_text_changed = False
        try:
            self.setPlainText(self._object.value)
        finally:
            self.notify_on_text_changed = True
        View.object_changed(self)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set([htypes.view.view_d('default'), *StringObject.dir_list[-1]], htypes.text_view.text_view())
        services.lcs.add([htypes.view.view_d('available'), *StringObject.dir_list[-1]], htypes.text_view.text_view())
        # services.lcs.add([htypes.view.view_d('available'), *StringObject.dir_list[-1]], htypes.text_view.text_edit_view())
        services.view_registry.register_actor(htypes.text_view.text_view, TextView.from_piece)
        services.view_registry.register_actor(htypes.text_view.text_edit_view, TextEditView.from_piece)
