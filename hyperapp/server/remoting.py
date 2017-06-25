import logging
from ..common.util import flatten, decode_path, encode_route
from ..common.htypes import tServerRoutes
from ..common.identity import PublicKey
from ..common.transport_packet import tTransportPacket
from ..common.packet_coders import packet_coders
from ..common.visual_rep import pprint
from ..common.requirements_collector import RequirementsCollector
from ..common.server_public_key_collector import ServerPksCollector
from .request import RequestBase
from .transport_session import TransportSessionList

log = logging.getLogger(__name__)


class Transport(object):

    def __init__(self, services):
        self._request_types = services.types.request
        self._core_types = services.types.core
        self._packet_types = services.types.packet
        self._resource_types = services.types.resource
        self._param_editor_types = services.types.param_editor
        self._route_storage = services.route_storage
        self._resources_loader = services.resources_loader
        self._type_module_repository = services.type_module_repository
        self._client_code_repository = services.client_code_repository

    def process_request_packet(self, iface_registry, server, peer, payload_encoding, packet):
        request_rec = packet_coders.decode(payload_encoding, packet.payload, self._request_types.client_packet)
        pprint(self._packet_types.aux_info, packet.aux_info)
        pprint(self._request_types.client_packet, request_rec)
        self._add_routes(packet.aux_info.routes)
        request = RequestBase.from_data(server, peer, self._request_types, self._core_types, iface_registry, request_rec)
        response_or_notification = server.process_request(request)
        if response_or_notification is None:
            return None
        aux_info = self.prepare_aux_info(response_or_notification)
        pprint(self._packet_types.aux_info, aux_info)
        pprint(self._request_types.server_packet, response_or_notification.to_data())
        payload = packet_coders.encode(payload_encoding, response_or_notification.to_data(), self._request_types.server_packet)
        return self._packet_types.packet(aux_info, payload)

    def _add_routes(self, routes):
        for srv_routes in routes:
            public_key = PublicKey.from_der(srv_routes.public_key_der)
            log.info('received routes for %s: %s',
                     public_key.get_short_id_hex(), ', '.join(encode_route(route) for route in srv_routes.routes))
            self._route_storage.add_routes(public_key, srv_routes.routes)

    def make_notification_packet(self, payload_encoding, notification):
        aux_info = self.prepare_aux_info(notification)
        pprint(self._packet_types.aux_info, aux_info)
        pprint(self._request_types.server_packet, notification.to_data())
        payload = packet_coders.encode(payload_encoding, notification.to_data(), self._request_types.server_packet)
        return self._packet_types.packet(aux_info, payload)

    def process_packet(self, server, peer, transport_packet_data):
        raise NotImplementedError(self.__class__)

    def prepare_aux_info(self, response_or_notification):
        collector = RequirementsCollector(self._core_types, self._param_editor_types)
        packet_requirements = collector.collect(self._request_types.server_packet, response_or_notification.to_data())
        resources1 = self._load_required_resources(packet_requirements)
        # resources themselves can contain requirements for more resources
        resource_requirements = collector.collect(self._resource_types.resource_rec_list, resources1)
        resources2 = self._load_required_resources(resource_requirements)
        requirements = packet_requirements + resource_requirements
        type_modules = self._type_module_repository.get_type_modules_by_requirements(requirements)
        modules = self._client_code_repository.get_modules_by_requirements(requirements)
        modules = []  # force separate request to code repository
        server_pks = ServerPksCollector().collect_public_key_ders(self._request_types.server_packet, response_or_notification.to_data())
        routes = [tServerRoutes(pk, self._route_storage.get_routes(PublicKey.from_der(pk))) for pk in server_pks]
        return self._packet_types.aux_info(
            requirements=requirements,
            type_modules=type_modules,
            modules=modules,
            routes=routes,
            resources=resources1 + resources2,
            )

    def _load_required_resources(self, requirements):
        return flatten([self._load_resource(id) for (registry, id) in requirements
                        if registry == 'resources'])

    def _load_resource(self, encoded_resource_id):
        return list(self._resources_loader.get_resources(decode_path(encoded_resource_id)))


class TransportRegistry(object):

    def __init__(self):
        self._id2transport = {}

    def register(self, id, transport):
        assert isinstance(id, str), repr(id)
        assert isinstance(transport, Transport), repr(transport)
        self._id2transport[id] = transport

    def resolve(self, id):
        return self._id2transport[id]


class Remoting(object):

    def __init__(self, iface_registry):
        self.iface_registry = iface_registry
        self.transport_registry = TransportRegistry()

    def process_packet(self, iface_registry, server, session_list, request_packet):
        assert isinstance(session_list, TransportSessionList), repr(session_list)
        assert isinstance(request_packet, tTransportPacket), repr(request_packet)
        transport = self.transport_registry.resolve(request_packet.transport_id)
        responses = transport.process_packet(iface_registry, server, session_list, request_packet.data)
        return [tTransportPacket(request_packet.transport_id, response_data)
                for response_data in responses]
