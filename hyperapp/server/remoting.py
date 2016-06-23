import logging
from ..common.util import encode_route
from ..common.htypes import tServerRoutes, tClientPacket, tServerPacket
from ..common.identity import PublicKey
from ..common.packet import tAuxInfo, tPacket
from ..common.transport_packet import tTransportPacket
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from ..common.requirements_collector import RequirementsCollector
from ..common.server_public_key_collector import ServerPksCollector
from .request import RequestBase
from .transport_session import TransportSessionList
from .code_repository import code_repository

log = logging.getLogger(__name__)


class Transport(object):

    def __init__( self, services ):
        self._route_storage = services.route_storage

    def process_request_packet( self, iface_registry, server, peer, payload_encoding, packet ):
        request_rec = packet_coders.decode(payload_encoding, packet.payload, tClientPacket)
        pprint(tAuxInfo, packet.aux_info)
        pprint(tClientPacket, request_rec)
        self._add_routes(packet.aux_info.routes)
        request = RequestBase.from_data(server, peer, iface_registry, request_rec)
        response_or_notification = server.process_request(request)
        if response_or_notification is None:
            return None
        aux_info = self.prepare_aux_info(response_or_notification)
        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, response_or_notification.to_data())
        payload = packet_coders.encode(payload_encoding, response_or_notification.to_data(), tServerPacket)
        return tPacket(aux_info, payload)

    def _add_routes( self, routes ):
        for srv_routes in routes:
            public_key = PublicKey.from_der(srv_routes.public_key_der)
            log.info('received routes for %s: %s',
                     public_key.get_short_id_hex(), ', '.join(encode_route(route) for route in srv_routes.routes))
            self._route_storage.add_routes(public_key, srv_routes.routes)

    def make_notification_packet( self, payload_encoding, notification ):
        aux_info = self.prepare_aux_info(notification)
        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, notification.to_data())
        payload = packet_coders.encode(payload_encoding, notification.to_data(), tServerPacket)
        return tPacket(aux_info, payload)

    def process_packet( self, server, peer, transport_packet_data ):
        raise NotImplementedError(self.__class__)

    def prepare_aux_info( self, response_or_notification ):
        requirements = RequirementsCollector().collect(tServerPacket, response_or_notification.to_data())
        modules = code_repository.get_modules_by_requirements(requirements)
        modules = []  # force separate request to code repository
        server_pks = ServerPksCollector().collect_public_key_ders(tServerPacket, response_or_notification.to_data())
        routes = [tServerRoutes(pk, self._route_storage.get_routes(PublicKey.from_der(pk))) for pk in server_pks]
        return tAuxInfo(
            requirements=requirements,
            modules=modules,
            routes=routes)


class TransportRegistry(object):

    def __init__( self ):
        self._id2transport = {}

    def register( self, id, transport ):
        assert isinstance(id, str), repr(id)
        assert isinstance(transport, Transport), repr(transport)
        self._id2transport[id] = transport

    def resolve( self, id ):
        return self._id2transport[id]


class Remoting(object):

    def __init__( self, iface_registry ):
        self._iface_registry = iface_registry
        self.transport_registry = TransportRegistry()

    def process_packet( self, iface_registry, server, session_list, request_packet ):
        assert isinstance(session_list, TransportSessionList), repr(session_list)
        assert isinstance(request_packet, tTransportPacket), repr(request_packet)
        transport = self.transport_registry.resolve(request_packet.transport_id)
        responses = transport.process_packet(iface_registry, server, session_list, request_packet.data)
        return [tTransportPacket(request_packet.transport_id, response_data)
                for response_data in responses]
