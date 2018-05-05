import uuid

from ..common.interface import packet as packet_types
from ..common.htypes import IfaceCommand
from ..common.url import Url, UrlWithRoutes
from .request import ClientNotification, Request
from .server import Server
from .module import Module


class ProxyMethod(object):

    def __init__(self, ref_registry, transport, iface, service_id, command):
        self._ref_registry = ref_registry
        self._transport = transport
        self._iface = iface
        self._service_id = service_id
        self._command = command

    async def __call__(self, *args, **kw):
        fields = (self._command.command_id,) + args
        if self._command.is_request:
            fields = (str(uuid.uuid4()),) + fields
        request = self._command.request_t(*fields, **kw)
        request_ref = self._ref_registry.register_object(self._command.request_t, request)
        self._transport.send(request_ref)


class RemotingProxy(object):

    def __init__(self, ref_registry, transport, iface, service_id):
        self._ref_registry = ref_registry
        self._transport = transport
        self._iface = iface
        self._service_id = service_id

    def __getattr__(self, name):
        command = self._iface.get_command(name)
        if not command:
            raise AttributeError(name)
        return ProxyMethod(self._ref_registry, self._transport, self._iface, self._service_id, command)


class ProxyFactory(object):

    def __init__(self, type_registry_registry, ref_registry, async_ref_resolver, transport_resolver):
        self._type_registry_registry = type_registry_registry
        self._ref_registry = ref_registry
        self._async_ref_resolver = async_ref_resolver
        self._transport_resolver = transport_resolver

    async def from_ref(self, ref):
        service = await self._async_ref_resolver.resolve_ref_to_object(ref, expected_type='hyper_ref.service_ref')
        iface = self._type_registry_registry.resolve_type(service.iface_full_type_name)
        transport = await self._transport_resolver.resolve(service.transport_ref)
        return RemotingProxy(self._ref_registry, transport, iface, service.service_id)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.proxy_factory = ProxyFactory(
            services.type_registry_registry,
            services.ref_registry,
            services.async_ref_resolver,
            services.transport_resolver,
            )
