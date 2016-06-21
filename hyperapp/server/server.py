import time
import logging
from ..common.util import encode_path
from ..common.htypes import tServerPacket
from ..common.identity import Identity
from ..common.endpoint import Url
from ..common.object_path_collector import ObjectPathCollector
from .request import RequestBase, Request, ServerNotification, Response
from .object import subscription
from . import module

log = logging.getLogger(__name__)


class Server(object):

    def __init__( self, identity, test_delay_sec=None ):
        assert isinstance(identity, Identity), repr(identity)
        self.identity = identity
        self.test_delay_sec = test_delay_sec  # float

    def get_identity( self ):
        return self.identity

    def get_public_key( self ):
        return self.identity.get_public_key()

    def make_url( self, iface, path ):
        return Url(iface, path, self.get_endpoint())

    def is_mine_url( self, url ):
        assert isinstance(url, Url), repr(url)
        return url.endpoint.public_key == self.get_public_key()

    def process_request( self, request ):
        assert isinstance(request, RequestBase), repr(request)
        object = self._resolve(request.iface, request.path)
        log.info('Object: %r', object)
        assert object, 'Object with iface=%r, path=%r not found' % (request.iface.iface_id, encode_path(request.path))
        if self.test_delay_sec:
            log.info('Test delay for %s sec...', self.test_delay_sec)
            time.sleep(self.test_delay_sec)
        response = object.process_request(request)
        response = self._prepare_response(object.__class__, request, response)
        if response is not None:
            self._subscribe_objects(request.peer.channel, response)
        return response

    def _resolve( self, iface, path ):
        return module.Module.run_resolver(iface, path)

    def _subscribe_objects( self, peer_channel, response ):
        collector = ObjectPathCollector()
        object_paths = collector.collect(tServerPacket, response.to_data())
        for path in object_paths:
            subscription.add(path, peer_channel)

    def _prepare_response( self, obj_class, request, response ):
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
