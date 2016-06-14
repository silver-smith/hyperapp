import asyncio
from PySide import QtCore, QtGui
from ..common.htypes import iface_registry
from ..common.endpoint import Url
from .command import Command
from .module import Module
from .proxy_object import execute_get_request


class ThisModule(Module):

    def get_commands( self ):
        return [Command('url_from_clipboard', 'Url from clipboard', 'Open url from clipboard', 'Alt+Ctrl+V')]

    def get_object_commands( self, object ):
        if object.get_url() is not None:
            return [Command('url_to_clipboard', 'Url to clipboard', 'Copy current url to clipboard', 'Alt+Ctrl+C')]
        return []

    @asyncio.coroutine
    def run_command( self, command_id ):
        if command_id == 'url_from_clipboard':
            return (yield from self.run_command_url_from_clipboard())
        return (yield from Module.run_command(self, command_id))

    @asyncio.coroutine
    def run_command_url_from_clipboard( self ):
        url_str = QtGui.QApplication.clipboard().text()
        url = Url.from_str(iface_registry, url_str)
        return execute_get_request(url)

    def run_object_command( self, command_id, object ):
        if command_id == 'url_to_clipboard':
            return self.run_command_url_to_clipboard(object)
        return Module.run_object_command(self, command_id, object, initiator_view)

    def run_command_url_to_clipboard( self, object ):
        url = object.get_url()
        assert url is not None
        QtGui.QApplication.clipboard().setText(url.to_str())


this_module = ThisModule()
