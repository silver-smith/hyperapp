import os
import unittest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from hyperapp.common.htypes import (
    tString,
    Field,
    RequestCmd,
    Interface,
    tClientPacket,
    tServerPacket,
    tRequest,
    tClientNotification,
#    register_iface,
    )
from hyperapp.common.htypes import IfaceRegistry
from hyperapp.common.transport_packet import tTransportPacket
from hyperapp.common.identity import Identity, PublicKey
from hyperapp.common.encrypted_packet import (
    tEncryptedPacket,
    tEncryptedInitialPacket,
    make_session_key,
    encrypt_initial_packet,
    decrypt_packet,
    )
from hyperapp.common.packet import tAuxInfo, tPacket
from hyperapp.common.packet_coders import packet_coders
from hyperapp.common.visual_rep import pprint
from hyperapp.server.request import RequestBase
from hyperapp.server.transport import transport_registry
import hyperapp.server.tcp_transport  # self-registering
import hyperapp.server.encrypted_transport  # self-registering
import hyperapp.server.module as module_mod
from hyperapp.server.object import Object, subscription
from hyperapp.server.server import Server
from hyperapp.server.transport_session import TransportSession, TransportSessionList


RSA_KEY_SIZE = 4096


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


class TestSession(TransportSession):
    pass


server_identity = Identity('rsa', rsa.generate_private_key(
    public_exponent=65537,
    key_size=RSA_KEY_SIZE,
    backend=default_backend()))


class ServerTest(unittest.TestCase):

    def setUp( self ):
        self.iface_registry = IfaceRegistry()
        self.iface_registry.register(test_iface)
        self.test_module = TestModule()  # self-registering
        self.server = Server(server_identity)
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

    def transport_id2encoding( self, transport_id ):
        if transport_id in ['tcp.cdr', 'tcp.json']:
            return transport_id.split('.')[1]
        else:
            return 'cdr'

    def encode_packet( self, transport_id, rec, type ):
        return packet_coders.encode(self.transport_id2encoding(transport_id), rec, type)

    def decode_packet( self, transport_id, data, type ):
        return packet_coders.decode(self.transport_id2encoding(transport_id), data, type)

    def encrypt_packet( self, session_list, transport_id, data ):
        if transport_id != 'encrypted_tcp':
            return data
        session = session_list.get_transport_session('test.encrypted_tcp')
        if session is None:
            session = TestSession()
            session.session_key = make_session_key()
            session_list.set_transport_session('test.encrypted_tcp', session)
        packet = encrypt_initial_packet(session.session_key, server_identity.get_public_key(), data)
        return self.encode_packet(transport_id, packet, tEncryptedInitialPacket)

    def decrypt_packet( self, session_list, transport_id, data ):
        if transport_id != 'encrypted_tcp':
            return data
        session = session_list.get_transport_session('test.encrypted_tcp')
        assert session is not None  # must be created by encrypt_packet
        encrypted_packet = self.decode_packet(transport_id, data, tEncryptedPacket)
        return decrypt_packet(session.session_key, encrypted_packet)

    def make_tcp_transport_request( self, session_list, transport_id, obj_id, command_id, **kw ):
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
            payload=self.encode_packet(transport_id, request, tClientPacket))
        request_packet_data = self.encode_packet(transport_id, request_packet, tPacket)
        transport_request = tTransportPacket.instantiate(
            transport_id=transport_id,
            data=self.encrypt_packet(session_list, transport_id, request_packet_data))
        return transport_request

    def make_tcp_transport_notification( self, session_list, transport_id, obj_id, command_id, **kw ):
        request = tClientNotification.instantiate(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name, obj_id],
            command_id=command_id,
            params=test_iface.get_request_params_type(command_id).instantiate(**kw),
            )
        print 'Sending client notification:'
        pprint(tClientPacket, request)
        request_packet = tPacket.instantiate(
            aux_info=tAuxInfo.instantiate(requirements=[], modules=[]),
            payload=self.encode_packet(transport_id, request, tClientPacket))
        request_packet_data = self.encode_packet(transport_id, request_packet, tPacket)
        transport_request = tTransportPacket.instantiate(
            transport_id=transport_id,
            data=self.encrypt_packet(session_list, transport_id, request_packet_data))
        return transport_request

    def decode_tcp_transport_response( self, session_list, transport_id, response_transport_packet ):
        self.assertEqual(transport_id, response_transport_packet.transport_id)
        packet_data = self.decrypt_packet(session_list, transport_id, response_transport_packet.data)
        response_packet = self.decode_packet(transport_id, packet_data, tPacket)
        print 'Received response:'
        pprint(tPacket, response_packet)
        response = self.decode_packet(transport_id, response_packet.payload, tServerPacket)
        pprint(tServerPacket, response)
        return response

    def execute_tcp_request( self, transport_id, obj_id, command_id, session_list=None, **kw ):
        if session_list is None:
            session_list = self.session_list
        transport_request = self.make_tcp_transport_request(session_list, transport_id, obj_id, command_id, **kw)
        response_transport_packet = transport_registry.process_packet(self.iface_registry, self.server, session_list, transport_request)
        response = self.decode_tcp_transport_response(session_list, transport_id, response_transport_packet)
        return response

    def execute_tcp_notification( self, transport_id, obj_id, command_id, session_list=None, **kw ):
        if session_list is None:
            session_list = self.session_list
        transport_request = self.make_tcp_transport_notification(session_list, transport_id, obj_id, command_id, **kw)
        response_transport_packet = transport_registry.process_packet(self.iface_registry, self.server, self.session_list, transport_request)
        assert response_transport_packet is None, repr(response_transport_packet)

    def test_tcp_cdr_echo_request( self ):
        self._test_tcp_echo_request('tcp.cdr')

    def test_tcp_json_echo_request( self ):
        self._test_tcp_echo_request('tcp.json')

    def test_encrypted_tcp_echo_request( self ):
        self._test_tcp_echo_request('encrypted_tcp')

    def _test_tcp_echo_request( self, transport_id ):
        response = self.execute_tcp_request(transport_id, obj_id='1', command_id='echo', test_param='hello')
        self.assertEqual('hello to you too', response.result.test_result)

    def test_tcp_cdr_broadcast_request( self ):
        self._test_broadcast_tcp_request('tcp.cdr')

    def test_tcp_json_broadcast_request( self ):
        self._test_broadcast_tcp_request('tcp.json')

    def test_encrypted_tcp_broadcast_request( self ):
        self._test_broadcast_tcp_request('encrypted_tcp')

    def _test_broadcast_tcp_request( self, transport_id ):
        message = 'hi, all!'
        obj_id = '1'

        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='subscribe')
        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='broadcast', message=message)

        self.assertEqual(1, len(response.updates))
        update = response.updates[0]
        self.assertEqual('test_iface', update.iface)
        self.assertEqual([TestModule.name, TestObject.class_name, obj_id], update.path)
        self.assertEqual(message, update.diff)

    def test_tcp_cdr_unsubscribe_notification_request( self ):
        self._test_unsubscribe_notification_tcp_request('tcp.cdr')

    def test_tcp_json_unsubscribe_notification_request( self ):
        self._test_unsubscribe_notification_tcp_request('tcp.json')

    def test_encrypted_tcp_unsubscribe_notification_request( self ):
        self._test_unsubscribe_notification_tcp_request('encrypted_tcp')

    def _test_unsubscribe_notification_tcp_request( self, transport_id ):
        obj_id = '1'
        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='subscribe')
        response = self.execute_tcp_notification(transport_id, obj_id=obj_id, command_id='unsubscribe')

    def test_tcp_cdr_server_notification( self ):
        self._test_tcp_server_notification('tcp.cdr')

    def test_tcp_json_server_notification( self ):
        self._test_tcp_server_notification('tcp.json')

    def test_encrypted_tcp_server_notification( self ):
        self._test_tcp_server_notification('encrypted_tcp')

    def _test_tcp_server_notification( self, transport_id ):
        message = 'hi, all!'
        obj_id = '1'
        session1 = TransportSessionList()
        session2 = TransportSessionList()

        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='subscribe', session_list=session1)
        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='subscribe', session_list=session2)

        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='broadcast', session_list=session2, message=message)

        notifications = session1.pull_notification_transport_packets()

        self.assertEqual(1, len(notifications))
        notification_packet = notifications[0]
        tTransportPacket.validate('<TransportPacket>', notification_packet)
        notification = self.decode_tcp_transport_response(session1, transport_id, notification_packet)
        self.assertEqual(1, len(notification.updates))
        update = notification.updates[0]
        self.assertEqual('test_iface', update.iface)
        self.assertEqual([TestModule.name, TestObject.class_name, obj_id], update.path)
        self.assertEqual(message, update.diff)
