import logging

from ..common.interface import hyper_ref as href_types
from ..common.interface import test as test_types
from .module import ServerModule

log = logging.getLogger(__name__)


ECHO_SERVICE_ID = 'echo'
MODULE_NAME = 'echo_service'


class EchoService(object):

    def __init__(self):
        self._subscribed_service_ref_set = set()

    def rpc_say(self, request, message):
        log.info('Echo.say(%r): message=%r', request, message)
        return request.make_response_result(message)

    def rpc_eat(self, request, message):
        log.info('Echo.eat(%r): message=%r', request, message)

    def rpc_notify(self, request, message):
        log.info('Echo.notify(%r): message=%r', request, message)

    def rpc_fail(self, request, message):
        raise test_types.test_error(message)

    def rpc_subscribe(self, request, service_ref):
        self._subscribed_service_ref_set.add(service_ref)

    def rpc_broadcast(self, request, message):
        for service_ref in self._subscribed_service_ref_set:
            pass


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ECHO_SERVICE_ID = ECHO_SERVICE_ID
        service = href_types.service(ECHO_SERVICE_ID, ['test', 'echo'])
        services.echo_service_ref = service_ref = services.ref_registry.register_object(service)
        self._echo_service = EchoService()
        services.service_registry.register(service_ref, lambda: self._echo_service)
