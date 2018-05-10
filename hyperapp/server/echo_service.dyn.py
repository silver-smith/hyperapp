import logging

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
        services.service_registry.register(ECHO_SERVICE_ID, EchoService)
        services.ECHO_SERVICE_ID = ECHO_SERVICE_ID
