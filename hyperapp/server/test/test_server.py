import unittest
from hyperapp.common.htypes import (
    tString,
    Field,
    RequestCmd,
    Interface,
    tClientPacket,
    tServerPacket,
    tRequest,
#    register_iface,
    )
from hyperapp.common.htypes import IfaceRegistry
from hyperapp.common.transport_packet import tTransportPacket
from hyperapp.common.packet import tAuxInfo, tPacket
from hyperapp.common.packet_coders import packet_coders
from hyperapp.common.visual_rep import pprint
from hyperapp.server.request import RequestBase
from hyperapp.server.transport import transport_registry
import hyperapp.server.tcp_transport  # self-registering
import hyperapp.server.module as module_mod
from hyperapp.server.object import Object
from hyperapp.server.server import Server


test_iface = Interface('test_iface', commands=[
    RequestCmd('echo', [Field('test_param', tString)], [Field('test_result', tString)]),
    ])


class TestObject(Object):

    class_name = 'test_object'

    def process_request( self, request ):
        if request.command_id == 'echo':
            return self.run_command_echo(request)
        return Object.process_request(self, request)

    def run_command_echo( self, request ):
        return request.make_response_result(test_result=request.params.test_param + ' to you too')


class TestModule(module_mod.Module):

    name = 'test_module'

    def __init__( self ):
        module_mod.Module.__init__(self, self.name)

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == TestObject.class_name:
            return TestObject()
        path.raise_not_found()

        
class ServerTest(unittest.TestCase):

    def setUp( self ):
        self.iface_registry = IfaceRegistry()
        self.iface_registry.register(test_iface)
        self.test_module = TestModule()  # self-registering
        self.server = Server()

    def test_simple_request( self ):
        request_data = tRequest.instantiate(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name],
            command_id='echo',
            params=test_iface.get_request_params_type('echo').instantiate(test_param='hello'),
            request_id='001',
            )
        pprint(tClientPacket, request_data)
        request = RequestBase.from_data(None, None, self.iface_registry, request_data)

        aux_info, response = self.server.process_request(request)

        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, response)
        self.assertEqual('hello to you too', response.result.test_result)

    def test_tcp_cdr_request( self ):
        self.check_tcp_request('cdr')

    def test_tcp_json_request( self ):
        self.check_tcp_request('json')

    def check_tcp_request( self, encoding ):
        request = tRequest.instantiate(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name],
            command_id='echo',
            params=test_iface.get_request_params_type('echo').instantiate(test_param='hello'),
            request_id='001',
            )
        pprint(tClientPacket, request)
        request_packet = tPacket.instantiate(
            aux_info=tAuxInfo.instantiate(requirements=[], modules=[]),
            payload=packet_coders.encode(encoding, request, tClientPacket))
        transport_request = tTransportPacket.instantiate(
            transport_id='tcp.%s' % encoding,
            data=packet_coders.encode(encoding, request_packet, tPacket))

        response_transport_packet = transport_registry.process_packet(self.iface_registry, self.server, None, transport_request)

        self.assertEqual('tcp.%s' % encoding, response_transport_packet.transport_id)
        response_packet = packet_coders.decode(encoding, response_transport_packet.data, tPacket)
        pprint(tPacket, response_packet)
        response = packet_coders.decode(encoding, response_packet.payload, tServerPacket)
        pprint(tServerPacket, response)
        self.assertEqual('hello to you too', response.result.test_result)
