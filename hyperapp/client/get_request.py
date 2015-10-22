import weakref
import uuid
from ..common.interface import get_iface
from ..common.request import Request
from .server import RespHandler


class GetRespHandler(RespHandler):

    def __init__( self, view ):
        RespHandler.__init__(self, iface=get_iface, command_id='get')
        self.view_wr = weakref.ref(view)

    def process_response( self, server, response ):
        view = self.view_wr()
        if view:
            view.process_handle_open(server, response.result)


def run_get_request( view, server, path ):
    command_id = 'get'
    resp_handler = GetRespHandler(view)
    request_id = str(uuid.uuid4())
    request = Request(server, get_iface, path, 'get', request_id)
    server.execute_request(request, resp_handler)
