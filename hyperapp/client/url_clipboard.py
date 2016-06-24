import asyncio
from PySide import QtCore, QtGui
from ..common.htypes import iface_registry
from ..common.url import UrlWithRoutes
from .command import Command
from .module import Module
from .proxy_object import execute_get_request


class ThisModule(Module):

    def __init__( self, services ):
        Module.__init__(self, services)
        self._remoting = services.remoting

    ## def get_commands( self ):
    ##     return [Command('url_from_clipboard', 'Url from clipboard', 'Open url from clipboard', 'Alt+Ctrl+V')]

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
        url = UrlWithRoutes.from_str(iface_registry, url_str)
        self._remoting.add_routes(url.public_key, url.routes)
        return execute_get_request(self._remoting, url)

    def run_object_command( self, command_id, object ):
        if command_id == 'url_to_clipboard':
            return self.run_command_url_to_clipboard(object)
        return Module.run_object_command(self, command_id, object)

    def run_command_url_to_clipboard( self, object ):
        url = object.get_url()
        assert url is not None
        enriched_url = self._remoting.add_routes_to_url(url)
        QtGui.QApplication.clipboard().setText(enrich_url.to_str())
