import os
import logging
from queue import Queue

from ..common.interface import error as error_types
from ..common.interface import packet as packet_types
from ..common.util import flatten
from ..common.request import Update
from ..common.transport_packet import tTransportPacket
from ..common.encrypted_packet import (
    ENCODING,
    POP_CHALLENGE_SIZE,
    tEncryptedPacket,
    tInitialEncryptedPacket,
    tSubsequentEncryptedPacket,
    tPopChallengePacket,
    tProofOfPossessionPacket,
    encrypt_subsequent_packet,
    decrypt_packet,
    )
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from ..common.identity import PublicKey
from .module import Module
from .request import NotAuthorizedError, PeerChannel, Peer, RequestBase, ServerNotification
from .remoting import Transport
from .transport_session import TransportSession

log = logging.getLogger(__name__)


MODULE_NAME = 'encrypted_transport'


class EncryptedTcpChannel(PeerChannel):

    def __init__(self, transport):
        self.transport = transport
        self.updates = Queue()  # Update list

    def _pop_all(self):
        updates = []
        while not self.updates.empty():
            updates.append(self.updates.get())
        return list(reversed(updates))

    def send_update(self, update):
        assert isinstance(update, Update), repr(update)
        log.info('    update to be sent to %r channel %s', self.transport.get_transport_id(), self.get_id())
        self.updates.put(update)

    def pop_updates(self):
        return self._pop_all()


class EncryptedTcpSession(TransportSession):

    def __init__(self, transport):
        assert isinstance(transport, EncryptedTcpTransport), repr(transport)
        TransportSession.__init__(self)
        self.transport = transport
        self.channel = EncryptedTcpChannel(transport)
        self.session_key = None
        self.pop_challenge = None  # str
        self.pop_challenge_sent = False
        self.pop_received = False
        self.peer_public_keys = []  # verified using pop
        self.requests_waiting_for_pop = []  # request Packet list

    def pull_notification_transport_packets(self):
        updates = self.channel._pop_all()
        if not updates:
            return []
        notification = ServerNotification(error_types, packet_types)
        for update in updates:
            notification.add_update(update)
        log.info('-- sending notification to %r channel %s', self.transport.get_transport_id(), self.get_id())
        notification_packet = self.transport.make_notification_packet(ENCODING, notification)
        notification_packet_data = packet_coders.encode(ENCODING, notification_packet, packet_types.packet)
        encrypted_packet = encrypt_subsequent_packet(self.session_key, notification_packet_data)
        packet_data = packet_coders.encode(ENCODING, encrypted_packet, tEncryptedPacket)
        return [tTransportPacket(self.transport.get_transport_id(), packet_data)]


class EncryptedTcpTransport(Transport):

    def __init__(self, services):
        Transport.__init__(self, services)
        self._iface_registry = services.iface_registry

    def get_transport_id(self):
        return 'encrypted_tcp'

    def register(self, registry):
        registry.register(self.get_transport_id(), self)

    def process_packet(self, iface_registry, server, session_list, data):
        session = session_list.get_transport_session(self.get_transport_id())
        if session is None:
           session = EncryptedTcpSession(self)
           session_list.set_transport_session(self.get_transport_id(), session)
        encrypted_packet = packet_coders.decode(ENCODING, data, tEncryptedPacket)
        pprint(tEncryptedPacket, encrypted_packet)
        if isinstance(encrypted_packet, tSubsequentEncryptedPacket):
            responses = self.process_encrypted_payload_packet(iface_registry, server, session, encrypted_packet)
        if isinstance(encrypted_packet, tProofOfPossessionPacket):
            responses = self.process_pop_packet(session, encrypted_packet)
        if session.pop_received:
            responses += flatten([self.process_postponed_request(server, session, request) for request in session.requests_waiting_for_pop])
            session.requests_waiting_for_pop = []
        if not session.pop_challenge_sent:
            responses.append(self.make_pop_challenge_packet(session))
            session.pop_challenge_sent = True
        for response in responses:
            pprint(tEncryptedPacket, response)
        return [packet_coders.encode(ENCODING, encrypted_packet, tEncryptedPacket)
                for encrypted_packet in responses]

    def process_encrypted_payload_packet(self, iface_registry, server, session, encrypted_packet):
        request_packet_data = self.decrypt_packet(server, session, encrypted_packet)
        request_packet = packet_coders.decode(ENCODING, request_packet_data, packet_types.packet)
        try:
            peer = Peer(session.channel, session.peer_public_keys)
            response_packet = self.process_request_packet(iface_registry, server, peer, ENCODING, request_packet)
            if response_packet is None:
                return []
            response_packet_data = packet_coders.encode(ENCODING, response_packet, packet_types.packet)
            return [encrypt_subsequent_packet(session.session_key, response_packet_data)]
        except NotAuthorizedError:
            if session.pop_received:
                raise
            session.requests_waiting_for_pop.append(request_packet)
            log.info('Request is postponed until POP is received: %r', request_packet)
            return []

    def process_postponed_request(self, server, session, request_packet):
        log.info('Reprocessing postponed request: %r', request_packet)
        peer = Peer(session.channel, session.peer_public_keys)
        response_packet = self.process_request_packet(self._iface_registry, server, peer, ENCODING, request_packet)
        packet_data = packet_coders.encode(ENCODING, response_packet, packet_types.packet)
        return [encrypt_subsequent_packet(session.session_key, packet_data)]

    def process_pop_packet(self, session, encrypted_packet):
        log.info('POP received')
        if encrypted_packet.challenge != session.pop_challenge:
            log.info('Error processing POP: challenge does not match')  # todo: return error
            return
        for rec in encrypted_packet.pop_records:
            public_key = PublicKey.from_der(rec.public_key_der)
            if public_key.verify(session.pop_challenge, rec.signature):
                session.peer_public_keys.append(public_key)
                log.info('Peer public key %s is verified', public_key.get_short_id_hex())
            else:
                log.info('Error processing POP record for %s: signature does not match', public_key.get_short_id_hex())  # todo: return error
        session.pop_received = True
        return []

    def decrypt_packet(self, server, session, encrypted_packet):
        if not isinstance(encrypted_packet, tInitialEncryptedPacket):
            assert session.session_key, tEncryptedPacket.get_object_class(encrypted_packet).id  # subsequent packet must not be first one
        session_key, plain_text = decrypt_packet(server.get_identity(), session.session_key, encrypted_packet)
        session.session_key = session_key
        return plain_text

    def make_pop_challenge_packet(self, session):
        log.info('sending pop challenge:')
        challenge = os.urandom(POP_CHALLENGE_SIZE//8)
        session.pop_challenge = challenge
        return tPopChallengePacket(
            challenge=challenge)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        EncryptedTcpTransport(services).register(services.remoting.transport_registry)
