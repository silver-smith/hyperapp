import logging
import uuid
import asyncio
from collections import namedtuple

from ..common.interface import error as error_types
from ..common.interface import hyper_ref as href_types
from ..common.util import full_type_name_to_str
from ..common.htypes import EncodableEmbedded
from ..common.ref import ref_repr, ref_list_repr
from ..common.visual_rep import pprint
from .request import Request
from .module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'remoting'

REQUEST_TIMEOUT_SEC = 5

PendingRequest = namedtuple('PendingRequest', 'iface command future')


class Remoting(object):

    def __init__(self, types, ref_registry, async_route_resolver, endpoint_registry, service_registry, transport_resolver):
        self._types = types
        self._ref_registry = ref_registry
        self._async_route_resolver = async_route_resolver
        self._service_registry = service_registry
        self._transport_resolver = transport_resolver
        self._pending_requests = {}  # request id -> PendingRequest
        self._my_endpoint_ref = endpoint_registry.register_endpoint(href_types.endpoint(
            service_id=str(uuid.uuid4())))

    async def send_request(self, service_ref, iface, command, params):
        log.info('Remoting: request %s %s to %s', full_type_name_to_str(iface.full_name), command.command_id, ref_repr(service_ref))
        transport_ref_set = await self._async_route_resolver.resolve(service_ref)
        assert transport_ref_set, 'No routes for service %s' % ref_repr(service_ref)
        assert len(transport_ref_set) == 1, ref_list_repr(transport_ref_set)  # todo: multiple route support
        transport = await self._transport_resolver.resolve(transport_ref_set.pop())
        if command.is_request:
            request_id = str(uuid.uuid4())
        else:
            request_id = None
        rpc_request = href_types.rpc_request(
            iface_full_type_name=iface.full_name,
            source_endpoint_ref=self._my_endpoint_ref,
            target_service_ref=service_ref,
            command_id=command.command_id,
            request_id=request_id,
            params=EncodableEmbedded(command.request, params),
            )
        pprint(rpc_request, title='RPC %s:' %command.request_type)
        pprint(params, title='params:')
        request_ref = self._ref_registry.register_object(rpc_request)
        transport.send(request_ref)
        if not command.is_request:
            return
        future = asyncio.Future()
        self._pending_requests[request_id] = PendingRequest(iface, command, future)
        try:
            log.info('Remoting: awaiting for response future...')
            result = (await asyncio.wait_for(future, timeout=REQUEST_TIMEOUT_SEC))
            log.info('Remoting: got result future: %r', result)
            return result
        finally:
            del self._pending_requests[request_id]

    def process_rpc_message(self, rpc_message_ref, rpc_message):
        log.info('Remoting: processing incoming RPC message:')
        pprint(rpc_message, indent=1)
        if isinstance(rpc_message, href_types.rpc_request):
            self._process_rpc_request(rpc_message)
        if isinstance(rpc_message, href_types.rpc_response):
            self._process_rpc_response(rpc_message)
        log.info('Remoting: processing incoming RPC message: done')

    def _process_rpc_request(self, rpc_request):
        iface = self._types.resolve(rpc_request.iface_full_type_name)
        command = iface.get(rpc_request.command_id)
        if not command:
            log.warning('Got request for unknown command %r for interface %s',
                            rpc_request.command_id, full_type_name_to_str(rpc_request.iface_full_type_name))
            return
        params = rpc_request.params.decode(command.request)
        pprint(params, title='params:')
        if command.is_request:
            log.warning('Got request, but only notifications are supported for server-to-client calls')
            return
        servant = self._service_registry.resolve(rpc_request.target_service_ref)
        request = Request()
        method_name = 'rpc_' + rpc_request.command_id
        method = getattr(servant, method_name, None)
        log.info('Calling %s %r', command.request_type, method)
        assert method, '%r does not implement method %s' % (servant, method_name)
        response = self._call_servant(command, method, request, params)
        assert not response, 'Only notifications are supported for now'

    def _call_servant(self, command, method, request, params):
        try:
            response = method(request, **params._asdict())
        except Exception as x:
            assert command.is_request  # todo: error handling for notifications
            if isinstance(x, error_types.error):
                error = x
            else:
                log.exception('Error processing %s %r:', command.request_type, method)
                error = error_types.server_error()
            return request.make_response(error=error)
        if not command.is_request:
            assert not response, 'No results are expected from notifications'
            return None
        if command.response.fields:
            assert response, 'Use request.make_response method to return results from requests'
        else:
            # No fields in response, servant is allowed to return None
            if not response:
                response = request.make_response_result()
        return response
        
    def _process_rpc_response(self, rpc_response):
        request = self._pending_requests.get(rpc_response.request_id)
        if not request:
            log.warning('No one is waiting for response %r; ignoring', rpc_response.request_id)
            return
        log.info('Response is for %s %s', full_type_name_to_str(request.iface.full_name), request.command.command_id)
        if rpc_response.is_succeeded:
            result_t = request.iface[request.command.command_id].response
            result = rpc_response.result_or_error.decode(result_t)
            pprint(result, title='Result:')
            request.future.set_result(result)
        else:
            error = rpc_response.result_or_error.decode(error_types.error)
            pprint(error, title='Error:')
            request.future.set_exception(error)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.remoting = remoting = Remoting(
            services.types,
            services.ref_registry,
            services.async_route_resolver,
            services.endpoint_registry,
            services.service_registry,
            services.transport_resolver,
            )
