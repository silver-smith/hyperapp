import uuid

from ..common.interface import hyper_ref as href_types
from ..common.htypes import EncodableEmbedded
from .module import ClientModule


MODULE_NAME = 'remoting'


class Remoting(object):

    def __init__(self, ref_registry, transport_resolver):
        self._ref_registry = ref_registry
        self._transport_resolver = transport_resolver

    async def send_request(self, transport_ref, iface, service_id, command, params):
        transport = await self._transport_resolver.resolve(transport_ref)
        if command.is_request:
            request_id = str(uuid.uuid4())
        else:
            request_id = None
        request = href_types.service_request(
            iface_full_type_name=iface.full_name,
            service_id=service_id,
            command_id=command.command_id,
            request_id=request_id,
            params=EncodableEmbedded(command.request, params),
            )
        request_ref = self._ref_registry.register_object(href_types.service_request, request)
        transport.send(request_ref)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.remoting = Remoting(services.ref_registry, services.transport_resolver)
