import abc
import os.path
import glob
from ..common.htypes import tEndpoint
from ..common.endpoint import Endpoint
from ..common.packet_coders import packet_coders


class RouteRepository(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def enumerate( self ):
        pass

    @abc.abstractmethod
    def add( self, endpoint ):
        pass


class FileRouteRepository(RouteRepository):

    fext = '.route.json'
    encoding = 'json_pretty'

    def __init__( self, dir ):
        self.dir = dir

    def enumerate( self ):
        for fpath in glob.glob(os.path.join(self.dir, '*' + self.fext)):
            yield self._load_item(fpath)

    def _load_item( self, fpath ):
        with open(fpath, 'rb') as f:
            data = f.read()
        rec = packet_coders.decode(self.encoding, data, tEndpoint)
        return Endpoint.from_data(rec)

    def add( self, endpoint ):
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        data = packet_coders.encode(self.encoding, endpoint.to_data(), tEndpoint)
        fpath = os.path.join(self.dir, endpoint.public_key.get_id_hex() + self.fext)
        with open(fpath, 'wb') as f:
            f.write(data)


class RouteStorage(object):

    instance = None  # todo: remove globals

    def __init__( self, repository ):
        assert isinstance(repository, RouteRepository), repr(repository)
        self._repository = repository
        self._server_id2routes = dict(
           (endpoint.public_key.get_id(), endpoint.routes) for endpoint in self._repository.enumerate())
        self.__class__.instance = self

    def add_endpoint_routes( self, endpoint ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        self._server_id2routes[endpoint.public_key.get_id()] = endpoint.routes
        self._repository.add(endpoint)

    def get_routes( self, server_public_id ):
        return self._server_id2routes.get(server_public_id.get_id(), [])
