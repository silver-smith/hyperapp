import logging

from hyperapp.common.module import Module
from . import htypes

log = logging.getLogger(__name__)


ECHO_SERVICE_ID = 'echo'
MODULE_NAME = 'echo_service'


class EchoService(object):

    def __init__(self, proxy_factory):
        self._proxy_factory = proxy_factory
        self._subscribed_service_ref_set = set()

    def rpc_say(self, request, message):
        log.info('Echo.say(%r): message=%r', request, message)
        return request.make_response_result(message)

    def rpc_eat(self, request, message):
        log.info('Echo.eat(%r): message=%r', request, message)

    def rpc_notify(self, request, message):
        log.info('Echo.notify(%r): message=%r', request, message)

    def rpc_fail(self, request, message):
        raise htypes.test.test_error(message)

    def rpc_subscribe(self, request, service_ref):
        self._subscribed_service_ref_set.add(service_ref)

    def rpc_broadcast(self, request, message):
        for service_ref in self._subscribed_service_ref_set:
            proxy = self._proxy_factory.from_ref(service_ref)
            proxy.notify(message)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ECHO_SERVICE_ID = ECHO_SERVICE_ID
        service = htypes.hyper_ref.service(ECHO_SERVICE_ID, ['test', 'echo'])
        services.echo_service_ref = service_ref = services.ref_registry.register_object(service)
        self._echo_service = EchoService(services.proxy_factory)
        services.service_registry.register(service_ref, lambda: self._echo_service)
