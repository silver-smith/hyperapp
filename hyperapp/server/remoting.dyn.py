import logging

from ..common.interface import hyper_ref as href_types
from .registry import Registry
from .request import Request, Response
from .module import ServerModule

log = logging.getLogger(__name__)


MODULE_NAME = 'remoting'


class ServiceRegistry(Registry):

    def resolve(self, service_id):
        rec = self._resolve(service_id)
        log.info('producing service for %r using %s(%s, %s)', service_id, rec.factory, rec.args, rec.kw)
        return rec.factory(*rec.args, **rec.kw)


class Remoting(object):

    def __init__(self, ref_registry, route_resolver, transport_resolver):
        self._ref_registry = ref_registry
        self._route_resolver = route_resolver
        self._transport_resolver = transport_resolver

    def process_incoming_bundle(self, bundle):
        self._ref_registry.register_bundle(bundle)
        transport_ref_set = self._route_resolver.resolve(bundle.ref)
        assert len(transport_ref_set) == 1, repr(transport_ref_set)  # todo: multiple transport support
        transport = self._transport_resolver.resolve(transport_ref_set.pop())
        assert 0, transport


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._ref_registry = services.ref_registry
        services.service_registry = service_registry = ServiceRegistry()
        services.remoting = Remoting(services.ref_registry, services.route_resolver, services.transport_resolver)
        services.transport_registry.register(href_types.service_request, self._process_request, services.types, service_registry)

    def _process_request(self, service_request, types, service_registry):
        iface = types.resolve(service_request.iface_full_type_name)
        command = iface[service_request.command_id]
        params = service_request.params.decode(command.request)
        servant = service_registry.resolve(service_request.service_id)
        request = Request(command)
        method = getattr(servant, 'remote_' + service_request.command_id, None)
        assert method, '%r does not implement method remote_%s' % (servant, service_request.command_id)
        response = method(request, **params._asdict())
        if not command.is_request:
            assert not response, 'No results are expected from notifications'
            return
        assert response, 'Use request.make_response... method to return results from requests'
        assert isinstance(response, Response)
        service_response = response.make_service_response(command, service_request.request_id)
        return service_response
    # todo: do not use capsule registry to produce responses, service_response is not the corresponding capsule for request ref
