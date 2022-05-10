import logging
import asyncio
import re

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class TextView(QtWidgets.QTextBrowser):

    @classmethod
    async def from_piece(cls, piece, adapter, add_dir_list):
        return cls(adapter)

    def __init__(self, adapter):
        super().__init__()
        self.setOpenLinks(False)
        # self._view_opener = view_opener
        self._adapter = adapter
        self.setHtml(self.text2html(adapter.text or ''))
        self.anchorClicked.connect(self.on_anchor_clicked)

    @property
    def state(self):
        return None

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
        self.setHtml(self.text2html(self.adapter.text))
        View.object_changed(self)

    # def __del__(self):
    #     log.info('~text_view %r', self)


class TextEditView(QtWidgets.QTextEdit):

    @classmethod
    async def from_piece(cls, piece, adapter, add_dir_list):
        return cls(adapter)

    def __init__(self, adapter):
        super().__init__()
        self._adapter = adapter
        self.notify_on_text_changed = True
        self.setPlainText(adapter.text)
        self.textChanged.connect(self._on_text_changed)

    @property
    def state(self):
        return None

    def _on_text_changed(self):
        if self.notify_on_text_changed:
            self._adapter.value_changed(self.toPlainText(), emitter_view=self)

    # todo: preserve cursor position
    def object_changed(self):
        self.notify_on_text_changed = False
        try:
            self.setPlainText(self._adapter.value)
        finally:
            self.notify_on_text_changed = True


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set([htypes.view.view_d('default'), htypes.text.text_d()], htypes.text_view.text_view())
        # services.available_view_registry.add_view(StringObject.dir_list[-1], htypes.text_view.text_view())
        # services.available_view_registry.add_view(StringObject.dir_list[-1], htypes.text_view.text_edit_view())
        services.view_registry.register_actor(htypes.text_view.text_view, TextView.from_piece)
        # services.view_registry.register_actor(htypes.text_view.text_edit_view, TextEditView.from_piece)
