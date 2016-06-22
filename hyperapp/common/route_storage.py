import abc
from ..common.util import is_list_list_inst
from ..common.identity import PublicKey


class RouteRepository(object, metaclass=abc.ABCMeta):

    # returns (PublicKey, route list) list/iterator
    @abc.abstractmethod
    def enumerate( self ):
        pass

    @abc.abstractmethod
    def add( self, endpoint ):
        pass

    def get( self, public_key ):
        return None


class RouteStorage(object):

    instance = None  # todo: remove globals

    def __init__( self, repository ):
        assert isinstance(repository, RouteRepository), repr(repository)
        self._repository = repository
        self._server_id2routes = dict((pk.get_id(), routes) for (pk, routes) in self._repository.enumerate())
        self.__class__.instance = self

    def add_routes( self, public_key, routes ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        assert is_list_list_inst(routes, str), repr(routes)
        self._server_id2routes[public_key.get_id()] = routes
        self._repository.add(public_key, routes)

    def get_routes( self, public_key ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        return self._server_id2routes.get(public_key.get_id(), []) \
          or self._repository.get(public_key)
