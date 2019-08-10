import logging
import asyncio
import re

from PySide import QtCore, QtGui

from hyperapp.client.module import ClientModule
from . import htypes
from .view import View
from .text_object import TextObject
from .view_registry import NotApplicable

log = logging.getLogger(__name__)


class TextView(View, QtGui.QTextBrowser):

    def __init__(self, view_opener, object):
        QtGui.QTextBrowser.__init__(self)
        View.__init__(self)
        self.setOpenLinks(False)
        self._view_opener = view_opener
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
        rec = await self.object.open_ref(url.path())
        if rec is not None:
            await self._view_opener.open_rec(rec)

    def object_changed(self):
        self.setHtml(self.text2html(self.object.text))
        View.object_changed(self)

    def __del__(self):
        log.info('~text_view %r', self)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._view_opener = services.view_opener
        services.view_registry.register_view_producer(self._produce_view)

    def _produce_view(self, type_ref, object, observer):
        if not isinstance(object, TextObject):
            raise NotApplicable(object)
        return TextView(self._view_opener, object)
