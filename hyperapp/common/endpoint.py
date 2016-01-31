import pickle
from .util import is_list_inst, is_list_list_inst
from .identity import PublicKey
from ..common.htypes import tEndpoint, tUrl


class Endpoint(object):

    @classmethod
    def load_from_file( cls, fpath ):
        with open(fpath, 'rb') as f:
            public_key_pem, routes = pickle.load(f)
        return cls(PublicKey.from_pem(public_key_pem), routes)

    @classmethod
    def from_data( cls, rec ):
        return cls(PublicKey.from_pem(rec.public_key_pem), rec.routes)

    def __init__( self, public_key, routes ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        assert is_list_list_inst(routes, basestring), repr(routes)
        self.public_key = public_key
        self.routes = routes

    def to_data( self ):
        return tEndpoint.instantiate(
            self.public_key.to_pem(),
            self.routes)

    def save_to_file( self, fpath ):
        with open(fpath, 'wb') as f:
            pickle.dump((self.public_key.to_pem(), self.routes), f)

    def __repr__( self ):
        return 'endpoint:%s' % self.public_key.get_short_id_hex()


class Url(object):

    @classmethod
    def from_data( cls, rec ):
        return cls(Endpoint.from_data(rec.endpoint), rec.path)

    def __init__( self, endpoint, path ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        assert is_list_inst(path, basestring), path
        self.endpoint = endpoint
        self.path = path

    def to_data( self ):
        return tUrl.instantiate(self.endpoint.to_data(), self.path)
