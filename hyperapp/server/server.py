import time
from ..common.htypes import tServerPacket
from ..common.identity import Identity
from ..common.packet import AuxInfo
from ..common.object_path_collector import ObjectPathCollector
from ..common.visual_rep import pprint
from ..common.requirements_collector import RequirementsCollector
from .request import RequestBase, Request, ServerNotification, Response
from .object import subscription
from .code_repository import code_repository
from . import module


class Server(object):

    def __init__( self, identity, test_delay_sec=None ):
        assert isinstance(identity, Identity), repr(identity)
        self.identity = identity
        self.test_delay_sec = test_delay_sec  # float

    def get_identity( self ):
        return self.identity

    def get_public_key( self ):
        return self.identity.get_public_key()

    def make_url( self, path ):
        return Url(self.get_endpoint(), path)

    def is_mine_url( self, url ):
        assert isinstance(url, Url), repr(url)
        return url.endpoint.public_key == self.get_public_key()

    def process_request( self, request ):
        assert isinstance(request, RequestBase), repr(request)
        path = request.path
        object = self._resolve(path)
        print 'Object:', object
        assert object, repr(path)  # 404: Path not found
        if self.test_delay_sec:
            print 'Test delay for %s sec...' % self.test_delay_sec
            time.sleep(self.test_delay_sec)
        response = object.process_request(request)
        response = self._prepare_response(object.__class__, request, response)
        if response is None:
            return None
        response_data = response.to_data()
        self._subscribe_objects(request.peer.channel, response_data)
        aux_info = self.prepare_aux_info(response_data)
        return (aux_info, response_data)

    def _resolve( self, path ):
        return module.Module.run_resolver(path)

    def _subscribe_objects( self, peer_channel, response_data ):
        collector = ObjectPathCollector()
        object_paths = collector.collect(tServerPacket, response_data)
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

    @staticmethod
    def prepare_aux_info( response_or_notification ):
        requirements = RequirementsCollector().collect(tServerPacket, response_or_notification)
        modules = code_repository.get_required_modules(requirements)
        modules = []  # force separate request to code repository
        return AuxInfo(
            requirements=requirements,
            modules=modules)

    ## def _send_notification( self ):
    ##     notification = ServerNotification()
    ##     while not self.updates_queue.empty():
    ##         notification.add_update(self.updates_queue.get())
    ##     self._wrap_and_send(PACKET_ENCODING, notification.encode())
    
    ## def _wrap_and_send( self, encoding, response_or_notification ):
    ##     aux = self._prepare_aux_info(response_or_notification)
    ##     packet = Packet.from_contents(encoding, response_or_notification, tServerPacket, aux)
    ##     print '%r to %s:%d:' % (packet, self.addr[0], self.addr[1])
    ##     pprint(tAuxInfo, aux)
    ##     pprint(tServerPacket, response_or_notification)
    ##     self.conn.send(packet)
