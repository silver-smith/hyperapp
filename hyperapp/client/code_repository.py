# code repository proxy

from PySide import QtCore
from ..common.interface.code_repository import code_repository_iface
from .server import Server
from .proxy_object import ObjRespHandler, ProxyObject


class PacketRespHandler(ObjRespHandler):

    def __init__( self, object, command_id, server, packet ):
        ObjRespHandler.__init__(self, object, command_id)
        self.server = server
        self.packet = packet

    def process_response( self, server, response ):
        object = self.object()
        if object:
            object.process_response(server, response, self)


class CodeRepositoryProxy(ProxyObject):

    def __init__( self, server ):
        path = ['code_repository', 'code_repository']
        ProxyObject.__init__(self, server, path, code_repository_iface)

    def get_required_modules_and_process_packet( self, requirements, server, packet ):
        command_id = 'get_required_modules'
        request = self.prepare_request(command_id, requirements=requirements)
        resp_handler = PacketRespHandler(self, command_id, server, packet)
        self.resp_handlers.add(resp_handler)
        self.server.execute_request(request, resp_handler)

    def process_response( self, server, response, resp_handler, initiator_view=None ):
        if resp_handler.command_id == 'get_required_modules':
            self.process_get_required_modules_response(resp_handler.server, resp_handler.packet, response.result)
        ProxyObject.process_response(self, server, response, resp_handler, initiator_view)

    def process_get_required_modules_response( self, server, packet, result ):
        app = QtCore.QCoreApplication.instance()
        app.add_modules(result.modules)
        print '-- reprocessing %r from %r' % (packet, server)
        app.reprocess_packet(server, packet)
