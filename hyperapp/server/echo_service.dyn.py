import logging

from ..common.interface import hyper_ref as href_types
from ..common.interface import test as test_types
from .module import ServerModule

log = logging.getLogger(__name__)


ECHO_SERVICE_ID = 'echo'
MODULE_NAME = 'echo_service'


class EchoService(object):

    def remote_say(self, request, message):
        log.info('Echo.say(%r): message=%r', request, message)
        return request.make_response_result(message)


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ECHO_SERVICE_ID = ECHO_SERVICE_ID
        service_ref = href_types.service_ref(['test', 'echo'], ECHO_SERVICE_ID)
        service_ref_ref = services.ref_registry.register_object(href_types.service_ref, service_ref)
        services.service_registry.register(service_ref_ref, EchoService)
