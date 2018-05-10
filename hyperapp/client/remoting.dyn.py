import logging
import uuid
import asyncio
from collections import namedtuple

from ..common.interface import hyper_ref as href_types
from ..common.htypes import EncodableEmbedded
from .module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'remoting'


PendingRequest = namedtuple('PendingRequest', 'iface command future')


class Remoting(object):

    def __init__(self, ref_registry, transport_resolver):
        self._ref_registry = ref_registry
        self._transport_resolver = transport_resolver
        self._pending_requests = {}  # request id -> PendingRequest

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
        if not command.is_request:
            return
        future = asyncio.Future()
        self._pending_requests[request_id] = PendingRequest(iface, command, future)
        try:
            return (await future)
        finally:
            del self._pending_requests[request_id]

    def process_response(self, service_response):
        assert service_response.is_succeeded  # todo
        request = self._pending_requests.get(service_response.request_id)
        if not request:
            log.warning('No one is waiting for response %r; ignoring', service_response.request_id)
            return
        response = service_response.result.decode(request.iface[request.command.command_id].response)
        future.set_result(response)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.remoting = remoting = Remoting(services.ref_registry, services.transport_resolver)
        services.transport_registry.register(href_types.service_response, remoting.process_response)
