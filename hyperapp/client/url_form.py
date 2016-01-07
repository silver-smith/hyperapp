# this module is outdated
# form allowing user to pick current url in stringified form and enter new url to open

import weakref
from .util import make_action
from .command import Command
from .object import Object
from .proxy_object import ProxyObject
from . import form_view as form
## from .get_request import run_get_request


class UrlFormObject(Object):

    def get_title( self ):
        return 'Url form'

    def get_commands( self ):
        return [Command('submit', 'Open', 'Open entered url', 'Return')]

    def run_command( self, command_id, initiator_view, **kw ):
        if command_id == 'submit':
            self.run_command_submit(initiator_view, **kw)
        else:
            Object.run_command(self, command_id, initiator_view, **kw)

    def run_command_submit( self, initiator_view, url ):
        run_get_request(initiator_view, decode_url(url))


def make_open_url_action( widget, window ):

    def run( window_wr ):
        window = window_wr()
        if not window: return
        view = window.get_current_view()
        object = view.get_object()
        url = object.get_url()
        if not url: return
        handle = form.Handle(UrlFormObject(),
                             [form.Field('url', form.StringFieldHandle(encode_url(url)))])
        view.open(handle)

    return make_action(widget, 'Open current url', 'Ctrl+U', run, weakref.ref(window))
