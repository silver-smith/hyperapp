import weakref
import uuid
from ..common.endpoint import Url
from ..common.interface import get_iface
from .request import Request
from .server import Server
from .view import View


class GetRequest(Request):

    def __init__( self, iface, path, command_id, request_id, initiator_view ):
        assert initiator_view is None or isinstance(initiator_view, View), repr(initiator_view)
        Request.__init__(self, iface, path, command_id, request_id)
        self.initiator_view_wr = weakref.ref(initiator_view)

    def process_response( self, server, response ):
        view = self.initiator_view_wr()
        if view:
            view.process_handle_open(response.result, server)


def run_get_request( view, url ):
    assert isinstance(url, Url), repr(url)
    server, path = Server.resolve_url(url)
    command_id = 'get'
    request_id = str(uuid.uuid4())
    request = GetRequest(get_iface, path, command_id, request_id, view)
    server.execute_request(request)
