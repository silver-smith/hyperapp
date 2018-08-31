import logging
import asyncio
import re
from PySide import QtCore, QtGui
from ..common.htypes import tString, Field
from ..common.interface import core as core_types
from .module import ClientModule
from . import view
from .text_object import TextObject

log = logging.getLogger(__name__)


MODULE_NAME = 'text_view'


class View(view.View, QtGui.QTextBrowser):

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry):
        object = await objimpl_registry.resolve(state.object)
        return cls(object, parent)

    @staticmethod
    def get_state_type():
        return this_module.state_type

    def __init__(self, object, parent):
        QtGui.QTextBrowser.__init__(self)
        view.View.__init__(self, parent)
        self.setOpenLinks(False)
        self.object = object
        self.setHtml(self.text2html(object.text or ''))
        self.anchorClicked.connect(self.on_anchor_clicked)
        self.object.subscribe(self)

    def get_state(self):
        return this_module.state_type('text_view', self.object.get_state())

    def get_title(self):
        return self.object.get_title()

    def get_object(self):
        return self.object

    def get_object_command_list(self, object, kinds=None):
        return object.get_command_list(TextObject.Mode.VIEW, kinds)

    def text2html(self, text):
        return re.sub(r'\[([^\]]+)\]', r'<a href="\1">\1</a>', text or '')

    def on_anchor_clicked(self, url):
        log.info('on_anchor_clicked url.path=%r', url.path())
        asyncio.async(self.open_url(url))

    async def open_url(self, url):
        handle = await self.object.open_ref(url.path())
        if handle:
            self.open(handle)

    def object_changed(self):
        self.setHtml(self.text2html(self.object.text))
        view.View.object_changed(self)

    def __del__(self):
        log.info('~text_view %r', self)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self.state_type = core_types.obj_handle
        services.view_registry.register('text_view', View.from_state, services.objimpl_registry)
