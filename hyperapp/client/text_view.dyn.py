import logging
import asyncio
import re

from PySide2 import QtCore, QtWidgets

from hyperapp.client.object import ObjectObserver
from hyperapp.client.module import ClientModule

from . import htypes
from .layout import ObjectLayout
from .view import View
from .text_object import TextObject

log = logging.getLogger(__name__)


class TextView(View, QtWidgets.QTextBrowser):

    def __init__(self, object):
        QtWidgets.QTextBrowser.__init__(self)
        View.__init__(self)
        self.setOpenLinks(False)
        # self._view_opener = view_opener
        self.object = object
        self.setHtml(self.text2html(object.text or ''))
        self.anchorClicked.connect(self.on_anchor_clicked)
        self.object.subscribe(self)

    def get_title(self):
        return self.object.get_title()

    def get_object(self):
        return self.object

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


class TextEditView(QtWidgets.QTextEdit, ObjectObserver):

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

    # def __del__(self):
    #     _log.info('~text_edit %r', self)


class TextViewLayout(ObjectLayout):

    @classmethod
    def from_data(cls, state, path, object, layout_watcher):
        return TextViewLayout(object, path, state.editable)

    def __init__(self, object, path, editable):
        super().__init__(path)
        self._object = object
        self._editable = editable

    @property
    def data(self):
        return htypes.text.text_edit_layout(self._editable)

    async def create_view(self, command_hub):
        return TextView(self._object)

    async def visual_item(self):
        if self._editable:
            tag = 'editable'
        else:
            tag = 'read-only'
        return self.make_visual_item(f'TextView/{tag}')


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.default_object_layouts.register('text', TextObject.category_list, self._make_text_layout_rec)
        services.available_object_layouts.register('text', TextObject.category_list, self._make_text_layout_rec)
        services.object_layout_registry.register_type(htypes.text.text_edit_layout, TextViewLayout.from_data)

    async def _make_text_layout_rec(self, object):
        return htypes.text.text_edit_layout(editable=False)
