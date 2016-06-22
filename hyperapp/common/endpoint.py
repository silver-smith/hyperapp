import pickle
import binascii
import base64
from .util import is_list_inst, is_list_list_inst
from .identity import PublicKey
from ..common.htypes import tEndpoint, tUrl, Interface
from ..common.packet_coders import packet_coders


class StringIsNotAnUrl(Exception):
    pass


class Endpoint(object):

    @classmethod
    def load_from_file( cls, fpath ):
        with open(fpath, 'rb') as f:
            public_key_pem, routes = pickle.load(f)
        return cls(PublicKey.from_pem(public_key_pem), routes)

    @classmethod
    def from_data( cls, rec ):
        return cls(PublicKey.from_der(rec.public_key_der), rec.routes)

    def __init__( self, public_key, routes ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        assert routes is None or is_list_list_inst(routes, str), repr(routes)
        self.public_key = public_key
        self.routes = routes or []

    def to_data( self ):
        return tEndpoint(
            self.public_key.to_der(),
            self.routes)

    def save_to_file( self, fpath ):
        with open(fpath, 'wb') as f:
            pickle.dump((self.public_key.to_pem(), self.routes), f)

    def __repr__( self ):
        return 'endpoint:%s' % self.public_key.get_short_id_hex()


class Url(object):

    str_encoding = 'cdr'

    @classmethod
    def from_data( cls, iface_registry, rec ):
        iface = iface_registry.resolve(rec.iface)
        return cls(iface, rec.path, Endpoint.from_data(rec.endpoint))

    @classmethod
    def from_str( cls, iface_registry, value ):
        try:
            data = base64.b64decode(value)
        except binascii.Error:
            raise StringIsNotAnUrl('Provided string is not stringified url')
        rec = packet_coders.decode(cls.str_encoding, data, tUrl)
        return cls.from_data(iface_registry, rec)

    def __init__( self, iface, path, endpoint ):
        assert isinstance(iface, Interface), repr(iface)
        assert is_list_inst(path, str), path
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        self.iface = iface
        self.path = path
        self.endpoint = endpoint

    def to_data( self ):
        return tUrl(self.iface.iface_id, self.path, self.endpoint.to_data())

    def to_str( self ):
        data = packet_coders.encode(self.str_encoding, self.to_data(), tUrl)
        return str(base64.b64encode(data), 'ascii')

    def clone( self, iface=None ):
        obj = Url(self.iface, self.path, self.endpoint)
        if iface is not None:
            assert isinstance(iface, Interface), repr(iface)
            obj.iface = iface
        return obj
