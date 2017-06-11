import os
import logging
import unittest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from hyperapp.common.htypes import (
    tString,
    Field,
    RequestCmd,
    Interface,
    )
from hyperapp.common.transport_packet import tTransportPacket
from hyperapp.common.identity import Identity, PublicKey
from hyperapp.common.encrypted_packet import (
    tEncryptedPacket,
    tSubsequentEncryptedPacket,
    tPopChallengePacket,
    tPopRecord,
    tProofOfPossessionPacket,
    make_session_key,
    encrypt_initial_packet,
    decrypt_packet,
    )
from hyperapp.common.packet_coders import packet_coders
from hyperapp.common.visual_rep import pprint
from hyperapp.common.module_manager import ModuleManager
from hyperapp.common.route_storage import RouteStorage
from hyperapp.common.services import ServicesBase
from hyperapp.server.module import Module
from hyperapp.server import route_storage
from hyperapp.server.request import NotAuthorizedError, PeerChannel, Peer, RequestBase
from hyperapp.server.remoting import Remoting
from hyperapp.server import tcp_transport
from hyperapp.server import encrypted_transport
from hyperapp.server.command import command
import hyperapp.server.module as module_mod
from hyperapp.server.object import Object, subscription
from hyperapp.server.server import Server
from hyperapp.server.transport_session import TransportSession, TransportSessionList
from hyperapp.common.test.util import PhonyRouteRepository

log = logging.getLogger(__name__)


DYN_MODULE_EXT = '.dyn.py'


logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')


test_iface = Interface('test_iface', commands=[
    RequestCmd('echo', [Field('test_param', tString)], [Field('test_result', tString)]),
    RequestCmd('check_ok', [Field('test_param', tString)], [Field('test_result', tString)]),
    RequestCmd('required_auth', result_fields=[Field('test_result', tString)]),
    RequestCmd('broadcast', [Field('message', tString)]),
    ],
    diff_type=tString)


authorized_peer_identity = Identity.generate(fast=True)


class TestObject(Object):

    class_name = 'test_object'
    iface = test_iface

    def __init__(self, test_error, module, id):
        Object.__init__(self)
        self._test_error = test_error
        self.module = module
        self.id = id

    def get_path(self):
        return self.module.make_path(self.class_name, self.id)

    @command('echo')
    def command_echo(self, request):
        return request.make_response_result(test_result=request.params.test_param + ' to you too')

    @command('check_ok')
    def command_check_ok(self, request):
        param = request.params.test_param
        if param == 'ok':
            return request.make_response_result(test_result='ok')
        else:
            raise self._test_error(param)

    @command('required_auth')
    def command_required_auth(self, request):
        pk = authorized_peer_identity.get_public_key()
        if pk not in request.peer.public_keys:
            raise NotAuthorizedError(pk)
        return request.make_response_result(test_result='ok')

    @command('broadcast')
    def command_broadcast(self, request):
        subscription.distribute_update(self.iface, self.get_path(), request.params.message)


class TestModule(module_mod.Module):

    name = 'test_module'

    def __init__(self, test_error):
        module_mod.Module.__init__(self, self.name)
        self._test_error = test_error

    def resolve(self, iface, path):
        objname = path.pop_str()
        if objname == TestObject.class_name:
            obj_id = path.pop_str()
            return TestObject(self._test_error, self, obj_id)
        path.raise_not_found()

        
class PhonyChannel(PeerChannel):

    def send_update(self):
        pass

    def pop_updates(self):
        return None


class PhonyResourcesLoader(object):

    def load_resources(self, resource_id):
        return []


class PhonyTypeRepository(object):

    def get_modules_by_requirements(self, requirements):
        return []


class PhonyModuleRepository(object):

    def get_module_by_requirement(self, registry, key):
        return None


class PhonyClientCodeRepository(object):

    def get_modules_by_requirements(self, requirements):
        return []


class TestSession(TransportSession):

    def pull_notification_transport_packets(self):
        return []


class Services(ServicesBase):

    def __init__(self):
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common/interface'))
        self.server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.dynamic_module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../dynamic_modules'))
        ServicesBase.init_services(self)
        self.route_storage = RouteStorage(PhonyRouteRepository())
        self.resources_loader = PhonyResourcesLoader()
        self.remoting = Remoting(self.iface_registry)
        self.client_code_repository = PhonyClientCodeRepository()
        self._load_type_modules([
            'resource',
            'core',
            'packet',
            'param_editor',
            'code_repository',
            ])
        self.module_manager = ModuleManager(self, self.type_registry_registry, self.types.packet)
        self.module_manager.register_meta_hook()
        try:
            self._load_server_modules()
            self._register_transports()
        except:
            self.module_manager.unregister_meta_hook()
            raise

    def _load_server_modules(self):
        for module_name in [
                'client_code_repository',
                ]:
            fpath = os.path.join(self.server_dir, module_name + DYN_MODULE_EXT)
            with open(fpath) as f:
                source = f.read()
            package = 'hyperapp.server'
            module = self.types.packet.module(id=module_name, package=package, deps=[], satisfies=[], source=source, fpath=fpath)
            self.module_manager.load_code_module(module)

    def _register_transports(self):
        for module in [tcp_transport, encrypted_transport]:
            module.register_transports(self.remoting.transport_registry, self)


server_identity = Identity.generate(fast=True)


class ServerTest(unittest.TestCase):

    def setUp(self):
        self.services = Services()
        self.types = self.services.types
        self.request_types = self.services.types.request
        self.iface_registry = self.services.iface_registry
        test_iface.register_types(self.request_types, self.services.types.core)
        self.iface_registry.register(test_iface)
        self._init_test_module()
        self.server = Server(self.request_types, self.services.types.core, server_identity)

    def _init_test_module(self):
        request_types = self.services.types.request
        self.test_error = request_types.error.register('test_error', base=request_types.client_error, fields=[
            Field('invalid_param', tString),
            ])
        self.test_module = TestModule(self.test_error)  # self-registering

    def tearDown(self):
        self.services.module_manager.unregister_meta_hook()


class ServerRequestHandlingTest(ServerTest):

    def test_simple_request(self):
        request_data = self.request_types.request(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name, '1'],
            command_id='echo',
            params=test_iface.get_request_params_type('echo')(test_param='hello'),
            request_id='001',
            )
        pprint(self.request_types.client_packet, request_data)
        request = RequestBase.from_data(None, Peer(PhonyChannel()),
                                        self.request_types, self.types.core, self.iface_registry, request_data)

        response = self.server.process_request(request)

        pprint(self.request_types.server_packet, response.to_data())
        self.assertEqual('hello to you too', response.result.test_result)

    def execute_check_ok_request(self, test_param):
        request_data = self.request_types.request(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name, '1'],
            command_id='check_ok',
            params=test_iface.get_request_params_type('check_ok')(test_param=test_param),
            request_id='002',
            )
        pprint(self.request_types.client_packet, request_data)
        request = RequestBase.from_data(None, Peer(PhonyChannel()),
                                        self.request_types, self.types.core, self.iface_registry, request_data)

        response = self.server.process_request(request)
        pprint(self.request_types.server_packet, response.to_data())
        return response

    def test_check_ok_result(self):
        response = self.execute_check_ok_request('ok')
        self.assertEqual('ok', response.result.test_result)

    def test_check_ok_error(self):
        response = self.execute_check_ok_request('fail me')
        assert isinstance(response.to_data(), self.request_types.error_response)
        assert isinstance(response.to_data().error, self.test_error)
        self.assertEqual('fail me', response.error.invalid_param)
        self.assertEqual('fail me', response.to_data().error.invalid_param)


class TransportRequestHandlingTest(ServerTest):

    def setUp(self):
        ServerTest.setUp(self)
        self.remoting = self.services.remoting
        self.session_list = TransportSessionList()

    def transport_id2encoding(self, transport_id):
        if transport_id in ['tcp.cdr', 'tcp.json']:
            return transport_id.split('.')[1]
        else:
            return 'cdr'

    def encode_packet(self, transport_id, rec, type):
        return packet_coders.encode(self.transport_id2encoding(transport_id), rec, type)

    def decode_packet(self, transport_id, data, type):
        return packet_coders.decode(self.transport_id2encoding(transport_id), data, type)

    def encrypt_packet(self, session_list, transport_id, data):
        if transport_id != 'encrypted_tcp':
            return data
        session = session_list.get_transport_session('test.encrypted_tcp')
        if session is None:
            session = TestSession()
            session.session_key = make_session_key()
            session_list.set_transport_session('test.encrypted_tcp', session)
        packet = encrypt_initial_packet(session.session_key, server_identity.get_public_key(), data)
        return self.encode_packet(transport_id, packet, tEncryptedPacket)

    def decrypt_transport_response_packets(self, session_list, transport_id, packets):
        if transport_id != 'encrypted_tcp':
            if len(packets) == 0:
                return None  # no response
            self.assertEqual(1, len(packets), repr(packets))
            self.assertEqual(transport_id, packets[0].transport_id)
            return packets[0].data
        session = session_list.get_transport_session('test.encrypted_tcp')
        assert session is not None  # must be created by encrypt_packet
        for packet in packets:
            self.assertEqual(transport_id, packet.transport_id)
            encrypted_packet = self.decode_packet(transport_id, packet.data, tEncryptedPacket)
            if isinstance(encrypted_packet, tSubsequentEncryptedPacket):
                session_key, packet_data = decrypt_packet(server_identity, session.session_key, encrypted_packet)
                return packet_data
        return None  # no response

    def make_tcp_transport_request(self, session_list, transport_id, obj_id, command_id, **kw):
        request = self.request_types.request(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name, obj_id],
            command_id=command_id,
            params=test_iface.get_request_params_type(command_id)(**kw),
            request_id='001',
            )
        log.info('Sending request:')
        pprint(self.request_types.client_packet, request)
        request_packet = self.types.packet.packet(
            aux_info=self.types.packet.aux_info(requirements=[], type_modules=[], modules=[], routes=[], resources=[]),
            payload=self.encode_packet(transport_id, request, self.request_types.client_packet))
        request_packet_data = self.encode_packet(transport_id, request_packet, self.types.packet.packet)
        transport_request = tTransportPacket(
            transport_id=transport_id,
            data=self.encrypt_packet(session_list, transport_id, request_packet_data))
        return transport_request

    def make_tcp_transport_notification(self, session_list, transport_id, obj_id, command_id, **kw):
        request = self.request_types.client_notification(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name, obj_id],
            command_id=command_id,
            params=test_iface.get_request_params_type(command_id)(**kw),
            )
        log.info('Sending client notification:')
        pprint(self.request_types.client_packet, request)
        request_packet = self.types.packet.packet(
            aux_info=self.types.packet.aux_info(requirements=[], type_modules=[], modules=[], routes=[], resources=[]),
            payload=self.encode_packet(transport_id, request, self.request_types.client_packet))
        request_packet_data = self.encode_packet(transport_id, request_packet, self.types.packet.packet)
        transport_request = tTransportPacket(
            transport_id=transport_id,
            data=self.encrypt_packet(session_list, transport_id, request_packet_data))
        return transport_request

    def decode_tcp_transport_response(self, session_list, transport_id, response_transport_packets):
        packet_data = self.decrypt_transport_response_packets(session_list, transport_id, response_transport_packets)
        if packet_data is None:
            return None  # no response
        response_packet = self.decode_packet(transport_id, packet_data, self.types.packet.packet)
        log.info('Received response:')
        pprint(self.types.packet.packet, response_packet)
        response = self.decode_packet(transport_id, response_packet.payload, self.request_types.server_packet)
        pprint(self.request_types.server_packet, response)
        return response

    def execute_tcp_request(self, transport_id, obj_id, command_id, session_list=None, **kw):
        if session_list is None:
            session_list = self.session_list
        transport_request = self.make_tcp_transport_request(session_list, transport_id, obj_id, command_id, **kw)
        response_transport_packets = self.remoting.process_packet(self.iface_registry, self.server, session_list, transport_request)
        response = self.decode_tcp_transport_response(session_list, transport_id, response_transport_packets)
        return response

    def execute_tcp_notification(self, transport_id, obj_id, command_id, session_list=None, **kw):
        if session_list is None:
            session_list = self.session_list
        transport_request = self.make_tcp_transport_notification(session_list, transport_id, obj_id, command_id, **kw)
        response_transport_packets = self.remoting.process_packet(self.iface_registry, self.server, self.session_list, transport_request)
        response = self.decode_tcp_transport_response(session_list, transport_id, response_transport_packets)
        self.assertIsNone(response)


    def test_tcp_cdr_echo_request(self):
        self._test_tcp_echo_request('tcp.cdr')

    def test_tcp_json_echo_request(self):
        self._test_tcp_echo_request('tcp.json')

    def test_encrypted_tcp_echo_request(self):
        self._test_tcp_echo_request('encrypted_tcp')

    def _test_tcp_echo_request(self, transport_id):
        response = self.execute_tcp_request(transport_id, obj_id='1', command_id='echo', test_param='hello')
        self.assertEqual('hello to you too', response.result.test_result)


    def test_tcp_cdr_check_ok_result_request(self):
        self._test_tcp_check_ok_result_request('tcp.cdr')

    def test_tcp_json_check_ok_result_request(self):
        self._test_tcp_check_ok_result_request('tcp.json')

    def test_encrypted_tcp_check_ok_result_request(self):
        self._test_tcp_check_ok_result_request('encrypted_tcp')

    def _test_tcp_check_ok_result_request(self, transport_id):
        response = self.execute_tcp_request(transport_id, obj_id='1', command_id='check_ok', test_param='ok')
        self.assertEqual('ok', response.result.test_result)


    def test_tcp_cdr_check_ok_error_request(self):
        self._test_tcp_check_ok_error_request('tcp.cdr')

    def test_tcp_json_check_ok_error_request(self):
        self._test_tcp_check_ok_error_request('tcp.json')

    def test_encrypted_tcp_check_ok_error_request(self):
        self._test_tcp_check_ok_error_request('encrypted_tcp')

    def _test_tcp_check_ok_error_request(self, transport_id):
        response = self.execute_tcp_request(transport_id, obj_id='1', command_id='check_ok', test_param='fail me')
        self.assertEqual('fail me', response.error.invalid_param)


    def test_tcp_cdr_broadcast_request(self):
        self._test_broadcast_tcp_request('tcp.cdr')

    def test_tcp_json_broadcast_request(self):
        self._test_broadcast_tcp_request('tcp.json')

    def test_encrypted_tcp_broadcast_request(self):
        self._test_broadcast_tcp_request('encrypted_tcp')

    def _test_broadcast_tcp_request(self, transport_id):
        message = 'hi, all!'
        obj_id = '1'

        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='subscribe')
        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='broadcast', message=message)

        self.assertEqual(1, len(response.updates))
        update = response.updates[0]
        self.assertEqual('test_iface', update.iface)
        self.assertEqual([TestModule.name, TestObject.class_name, obj_id], update.path)
        self.assertEqual(message, update.diff)

    def test_tcp_cdr_unsubscribe_notification_request(self):
        self._test_unsubscribe_notification_tcp_request('tcp.cdr')

    def test_tcp_json_unsubscribe_notification_request(self):
        self._test_unsubscribe_notification_tcp_request('tcp.json')

    def test_encrypted_tcp_unsubscribe_notification_request(self):
        self._test_unsubscribe_notification_tcp_request('encrypted_tcp')

    def _test_unsubscribe_notification_tcp_request(self, transport_id):
        obj_id = '1'
        response = self.execute_tcp_request(transport_id, obj_id=obj_id, command_id='subscribe')
        response = self.execute_tcp_notification(transport_id, obj_id=obj_id, command_id='unsubscribe')

    def test_tcp_cdr_server_notification(self):
        self._test_tcp_server_notification('tcp.cdr')

    def test_tcp_json_server_notification(self):
        self._test_tcp_server_notification('tcp.json')

    def test_encrypted_tcp_server_notification(self):
        self._test_tcp_server_notification('encrypted_tcp')

    def _test_tcp_server_notification(self, transport_id):
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
        assert isinstance(notification_packet, tTransportPacket), repr(notification_packet)
        notification = self.decode_tcp_transport_response(session1, transport_id, [notification_packet])
        self.assertEqual(1, len(notification.updates))
        update = notification.updates[0]
        self.assertEqual('test_iface', update.iface)
        self.assertEqual([TestModule.name, TestObject.class_name, obj_id], update.path)
        self.assertEqual(message, update.diff)

    def pick_pop_channelge_from_responses(self, transport_id, response_transport_packets):
        for packet in response_transport_packets:
            encrypted_packet = self.decode_packet(transport_id, packet.data, tEncryptedPacket)
            if isinstance(encrypted_packet, tPopChallengePacket):
                return encrypted_packet.challenge
        self.fail('No challenge packet in response')

    def encode_pop_transport_request(self, transport_id, challenge, pop_records):
        pop_packet = tProofOfPossessionPacket(challenge, pop_records)
        pop_packet_data = self.encode_packet(transport_id, pop_packet, tEncryptedPacket)
        return tTransportPacket(transport_id=transport_id, data=pop_packet_data)

    def test_proof_of_possession(self):
        transport_id = 'encrypted_tcp'
        transport_request = self.make_tcp_transport_request(self.session_list, transport_id, obj_id='1', command_id='echo', test_param='hi')
        response_transport_packets = self.remoting.process_packet(self.iface_registry, self.server, self.session_list, transport_request)
        challenge = self.pick_pop_channelge_from_responses(transport_id, response_transport_packets)

        identity_1 = Identity.generate(fast=True)
        identity_2 = Identity.generate(fast=True)

        pop_record_1 = tPopRecord(
            identity_1.get_public_key().to_der(),
            identity_1.sign(challenge))
        pop_record_2 = tPopRecord(
            identity_2.get_public_key().to_der(),
            identity_2.sign(challenge + b'x'))  # make invlid signature; verification must fail
        transport_request = self.encode_pop_transport_request(transport_id, challenge, [pop_record_1, pop_record_2])

        response_transport_packets = self.remoting.process_packet(self.iface_registry, self.server, self.session_list, transport_request)

        session = self.session_list.get_transport_session(transport_id)
        self.assertIn(identity_1.get_public_key(), session.peer_public_keys)
        self.assertNotIn(identity_2.get_public_key(), session.peer_public_keys)

    # when NotAuthorizedError raised in first request before pop is returned, that request must be reprocessed when pop is processed
    def test_unauthorized_request_reprocess(self):
        transport_id = 'encrypted_tcp'
        transport_request = self.make_tcp_transport_request(self.session_list, transport_id, obj_id='1', command_id='required_auth')
        response_transport_packets = self.remoting.process_packet(
            self.iface_registry, self.server, self.session_list, transport_request)
        challenge = self.pick_pop_channelge_from_responses(transport_id, response_transport_packets)

        pop_record = tPopRecord(
            authorized_peer_identity.get_public_key().to_der(),
            authorized_peer_identity.sign(challenge))
        transport_request = self.encode_pop_transport_request(transport_id, challenge, [pop_record])

        response_transport_packets = self.remoting.process_packet(
            self.iface_registry, self.server, self.session_list, transport_request)

        response = self.decode_tcp_transport_response(self.session_list, transport_id, response_transport_packets)
        self.assertIsNotNone(response)  # now, after pop is received, first request must be processed
        self.assertEqual('ok', response.result.test_result)


if __name__ == '__main__':
    unittest.main()
