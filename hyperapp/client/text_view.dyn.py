import logging
import asyncio
import re

from PySide2 import QtCore, QtWidgets

from . import htypes
from .object import ObjectObserver
from .layout import ObjectLayout
from .view import View
from .string_object import StringObject
from .module import ClientModule

log = logging.getLogger(__name__)


class TextView(View, QtWidgets.QTextBrowser):

    @classmethod
    async def from_piece(cls, piece, object, lcs):
        return cls(object)

    def __init__(self, object):
        QtWidgets.QTextBrowser.__init__(self)
        View.__init__(self)
        self.setOpenLinks(False)
        # self._view_opener = view_opener
        self.object = object
        self.setHtml(self.text2html(object.value or ''))
        self.anchorClicked.connect(self.on_anchor_clicked)
        self.object.subscribe(self)

    @property
    def piece(self):
        return htypes.text.text_view()

    @property
    def state(self):
        return None

    @property
    def title(self):
        return self.object.title

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

    @property
    def title(self):
        return self.object.title

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
    async def from_data(cls, state, path, layout_watcher, mosaic, async_web):
        object_type = await async_web.summon(state.object_type_ref)
        return TextViewLayout(mosaic, path, object_type, state.command_list, state.editable)

    def __init__(self, mosaic, path, object_type, command_list_data, editable):
        super().__init__(mosaic, path, object_type, command_list_data)
        self._editable = editable

    @property
    def piece(self):
        return htypes.text.text_edit_layout(self._object_type_ref, self._command_list_data, self._editable)

    async def create_view(self, command_hub, object):
        return TextView(object)

    async def visual_item(self):
        if self._editable:
            tag = 'editable'
        else:
            tag = 'read-only'
        return self.make_visual_item(f'TextView/{tag}')


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set(StringObject.dir_list[-1], htypes.text.text_view())
        services.view_registry.register_actor(htypes.text.text_view, TextView.from_piece, services.lcs)
