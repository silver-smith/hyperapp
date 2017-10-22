import time
import logging
import traceback
from ..common.util import encode_path
from ..common.identity import Identity
from ..common.url import Url
from ..common.object_path_collector import ObjectPathCollector
from .request import NotAuthorizedError, RequestBase, Request, ServerNotification, Response
from .object import subscription

log = logging.getLogger(__name__)


class Server(object):

    @classmethod
    def create(cls, services, start_args):
        return cls(
            services.types.packet,
            services.types.core,
            services.module_registry,
            services.iface_registry,
            start_args.identity,
            start_args.test_delay,
            )

    def __init__(self, packet_types, core_types, module_registry, iface_registry, identity, test_delay_sec=None):
        assert isinstance(identity, Identity), repr(identity)
        self._packet_types = packet_types
        self._core_types = core_types
        self._module_registry = module_registry
        self._iface_registry = iface_registry
        self.identity = identity
        self.test_delay_sec = test_delay_sec  # float

    def get_identity(self):
        return self.identity

    def get_public_key(self):
        return self.identity.get_public_key()

    def make_url(self, iface, path):
        return Url(iface, self.identity.get_public_key(), path)

    def is_mine_url(self, url):
        assert isinstance(url, Url), repr(url)
        return url.public_key == self.get_public_key()

    def process_request(self, request):
        assert isinstance(request, RequestBase), repr(request)
        object = self._resolve(request.iface, request.path)
        log.info('Object: %r', object)
        assert object, 'Object with iface=%r, path=%r not found' % (request.iface.iface_id, encode_path(request.path))
        if self.test_delay_sec:
            log.info('Test delay for %s sec...', self.test_delay_sec)
            time.sleep(self.test_delay_sec)
        response = self.process_object_request(object, request)
        response = self._prepare_response(object.__class__, request, response)
        if response is not None:
            self._subscribe_objects(request.peer.channel, response)
        return response

    def process_object_request(self, object, request):
        try:
            return object.process_request(request)
        except NotAuthorizedError:
            raise
        except Exception as x:
            if isinstance(x, self._packet_types.error):
                error = x
            else:
                traceback.print_exc()
                error = self._packet_types.server_error()
            return request.make_response(error=error)

    def _resolve(self, iface, path):
        return self._module_registry.run_resolver(iface, path)

    def _subscribe_objects(self, peer_channel, response):
        collector = ObjectPathCollector(self._packet_types, self._core_types, self._iface_registry)
        object_paths = collector.collect(self._packet_types.payload, response.to_data())
        for path in object_paths:
            subscription.add(path, peer_channel)

    def _prepare_response(self, obj_class, request, response):
        assert response is None or isinstance(response, Response), \
          'Server commands must return a response, but %s.%s command returned %r' % (obj_class.__name__, request.command_id, response)
        if response is None and isinstance(request, Request):
            response = request.make_response()  # client need a response to cleanup waiting response handler
        updates = request.peer.channel.pop_updates()
        if response is None and updates:
            response = ServerNotification()
        for update in updates or []:
            response.add_update(update)
        return response
