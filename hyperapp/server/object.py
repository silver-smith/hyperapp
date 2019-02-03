import logging
from operator import attrgetter

from ..common.util import is_list_inst, encode_path
# from ..common.htypes import (
#     tString,
#     tInt,
#     Field,
#     Interface,
#     )
#from ..common.request import Update
#from ..common.diff import Diff
from .util import WeakValueMultiDict
from .command import Commander

log = logging.getLogger(__name__)


MIN_ROWS_RETURNED = 100


class Subscription(object):

    def __init__(self):
        self.path2channel = WeakValueMultiDict()  # path -> Channel

    def add(self, path, peer_channel):
        log.info('-- subscribing %r %r', path, peer_channel.get_id())
        self.path2channel.add(encode_path(path), peer_channel)

    def remove(self, path, peer_channel):
        log.info('-- unsubscribing %r %r', path, peer_channel.get_id())
        self.path2channel.remove(encode_path(path), peer_channel)

    def distribute_update(self, iface, path, diff):
        assert isinstance(iface, Interface), repr(iface)
        assert is_list_inst(path, str), repr(path)
        assert isinstance(diff, Diff), repr(diff)
        update = Update(iface, path, diff)
        log.info('-- distributing update:')
        update.pprint()
        for peer_channel in self.path2channel.get(encode_path(path)):
            log.info('-- sending update to %r', peer_channel.get_id())
            peer_channel.send_update(update)


subscription = Subscription()


class Object(Commander):

    facets = None

    def __init__(self, core_types=None):
        Commander.__init__(self, commands_kind='object')
        self._core_types = core_types

    def get_path(self):
        raise NotImplementedError(self.__class__)

    def get_facets(self, iface=None):
        facets = []
        if not iface:
            iface = self.iface
            facets += self.facets or []
        facets += [iface]
        if iface.base:
            return facets + self.get_facets(iface.base)
        else:
            return facets

    def get(self, request):
        path = self.get_path()
        assert is_list_inst(path, str), '%s.get_path must return list of strings, but returned: %r' % (self.__class__.__name__, path)
        return self.iface.Object(
            impl_id=self.impl_id,
            public_key_der=request.me.get_public_key().to_der(),
            iface=self.iface.iface_id,
            facets=[facet.iface_id for facet in self.get_facets()],
            path=path,
            contents=self.get_contents(request),
            )

    def get_contents(self, request, **kw):
        return self.iface.Contents(**kw)

    def get_handle(self, request):
        raise NotImplementedError(self.__class__)

    def process_request(self, request):
        command_id = request.command_id
        if command_id == 'get':
            return self.process_request_get(request)
        if command_id == 'subscribe':
            return self.process_request_subscribe(request)
        elif command_id == 'unsubscribe':
            self.unsubscribe(request)
        else:
            command = self.get_command(command_id)
            assert command, repr(command_id)  # Unknown command
            return command.run(request)

    def process_request_get(self, request):
        return request.make_response_handle(self.get_handle(request))

    def process_request_subscribe(self, request):
        self.subscribe(request)
        return request.make_response(self.get_contents(request))

    def subscribe(self, request):
        subscription.add(self.get_path(), request.peer.channel)

    def unsubscribe(self, request):
        subscription.remove(self.get_path(), request.peer.channel)
