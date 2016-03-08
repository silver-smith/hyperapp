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
from hyperapp.server.object import Object, subscription
from hyperapp.server.server import Server
from hyperapp.server.transport_session import TransportSessionList


test_iface = Interface('test_iface', commands=[
    RequestCmd('echo', [Field('test_param', tString)], [Field('test_result', tString)]),
    RequestCmd('broadcast', [Field('message', tString)]),
    ],
    diff_type=tString)


class TestObject(Object):

    class_name = 'test_object'
    iface = test_iface

    def __init__( self, module, id ):
        Object.__init__(self)
        self.module = module
        self.id = id

    def get_path( self ):
        return self.module.make_path(self.class_name, self.id)

    def process_request( self, request ):
        if request.command_id == 'echo':
            return self.run_command_echo(request)
        if request.command_id == 'broadcast':
            return self.run_command_broadcast(request)
        return Object.process_request(self, request)

    def run_command_echo( self, request ):
        return request.make_response_result(test_result=request.params.test_param + ' to you too')

    def run_command_broadcast( self, request ):
        subscription.distribute_update(self.iface, self.get_path(), request.params.message)


class TestModule(module_mod.Module):

    name = 'test_module'

    def __init__( self ):
        module_mod.Module.__init__(self, self.name)

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == TestObject.class_name:
            obj_id = path.pop_str()
            return TestObject(self, obj_id)
        path.raise_not_found()

        
class PhonyChannel(object):

    def send_update( self ):
        pass

    def pop_updates( self ):
        return None


class ServerTest(unittest.TestCase):

    def setUp( self ):
        self.iface_registry = IfaceRegistry()
        self.iface_registry.register(test_iface)
        self.test_module = TestModule()  # self-registering
        self.server = Server()
        self.session_list = TransportSessionList()

    def test_simple_request( self ):
        request_data = tRequest.instantiate(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name, '1'],
            command_id='echo',
            params=test_iface.get_request_params_type('echo').instantiate(test_param='hello'),
            request_id='001',
            )
        pprint(tClientPacket, request_data)
        request = RequestBase.from_data(None, PhonyChannel(), self.iface_registry, request_data)

        aux_info, response = self.server.process_request(request)

        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, response)
        self.assertEqual('hello to you too', response.result.test_result)

    def make_tcp_transport_request( self, encoding, obj_id, command_id, **kw ):
        request = tRequest.instantiate(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name, obj_id],
            command_id=command_id,
            params=test_iface.get_request_params_type(command_id).instantiate(**kw),
            request_id='001',
            )
        print 'Sending request:'
        pprint(tClientPacket, request)
        request_packet = tPacket.instantiate(
            aux_info=tAuxInfo.instantiate(requirements=[], modules=[]),
            payload=packet_coders.encode(encoding, request, tClientPacket))
        transport_request = tTransportPacket.instantiate(
            transport_id='tcp.%s' % encoding,
            data=packet_coders.encode(encoding, request_packet, tPacket))
        return transport_request

    def decode_tcp_transport_response( self, encoding, response_transport_packet ):
        self.assertEqual('tcp.%s' % encoding, response_transport_packet.transport_id)
        response_packet = packet_coders.decode(encoding, response_transport_packet.data, tPacket)
        print 'Received response:'
        pprint(tPacket, response_packet)
        response = packet_coders.decode(encoding, response_packet.payload, tServerPacket)
        pprint(tServerPacket, response)
        return response

    def execute_tcp_request( self, encoding, obj_id, command_id, **kw ):
        transport_request = self.make_tcp_transport_request(encoding, obj_id, command_id, **kw)
        response_transport_packet = transport_registry.process_packet(self.iface_registry, self.server, self.session_list, transport_request)
        response = self.decode_tcp_transport_response(encoding, response_transport_packet)
        return response

    def test_tcp_cdr_echo_request( self ):
        self._test_tcp_echo_request('cdr')

    def test_tcp_json_echo_request( self ):
        self._test_tcp_echo_request('json')

    def _test_tcp_echo_request( self, encoding ):
        response = self.execute_tcp_request(encoding, obj_id='1', command_id='echo', test_param='hello')
        self.assertEqual('hello to you too', response.result.test_result)

    def test_tcp_cdr_broadcast_request( self ):
        self._test_broadcast_tcp_request('cdr')

    def test_tcp_json_broadcast_request( self ):
        self._test_broadcast_tcp_request('json')

    def _test_broadcast_tcp_request( self, encoding ):
        message = 'hi, all!'
        obj_id = '1'

        response = self.execute_tcp_request(encoding, obj_id=obj_id, command_id='subscribe')
        response = self.execute_tcp_request(encoding, obj_id=obj_id, command_id='broadcast', message=message)

        self.assertEqual(1, len(response.updates))
        update = response.updates[0]
        self.assertEqual('test_iface', update.iface)
        self.assertEqual([TestModule.name, TestObject.class_name, obj_id], update.path)
        self.assertEqual(message, update.diff)
