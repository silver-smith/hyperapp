import pickle
import binascii
import base64
from .util import is_list_inst, is_list_list_inst
from .identity import PublicKey
from ..common.htypes import tUrl, tUrlWithRoutes, Interface, IfaceRegistry
from ..common.packet_coders import packet_coders


class StringIsNotAnUrl(Exception):
    pass


class Url(object):

    type = tUrl
    str_encoding = 'cdr'

    @classmethod
    def from_data( cls, iface_registry, rec ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        iface = iface_registry.resolve(rec.iface)
        public_key = PublicKey.from_der(rec.public_key_der)
        return cls(iface, public_key, rec.path)

    @classmethod
    def from_str( cls, iface_registry, value ):
        try:
            data = base64.b64decode(value)
        except binascii.Error:
            raise StringIsNotAnUrl('Provided string is not stringified url')
        rec = packet_coders.decode(cls.str_encoding, data, cls.type)
        return cls.from_data(iface_registry, rec)

    def __init__( self, iface, public_key, path ):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(public_key, PublicKey), repr(public_key)
        assert is_list_inst(path, str), path
        self.iface = iface
        self.public_key = public_key
        self.path = path

    def to_data( self ):
        return self.type(self.iface.iface_id, self.public_key.to_der(), self.path)

    def to_str( self ):
        data = packet_coders.encode(self.str_encoding, self.to_data(), self.type)
        return str(base64.b64encode(data), 'ascii')

    def clone( self, iface=None ):
        obj = Url(self.iface, self.public_key, self.path)
        if iface is not None:
            assert isinstance(iface, Interface), repr(iface)
            obj.iface = iface
        return obj

    def clone_with_routes( self, routes ):
        return UrlWithRoutes(self.iface, self.public_key, self.path, routes)


class UrlWithRoutes(Url):

    type = tUrlWithRoutes

    @classmethod
    def load_from_file( cls, iface_registry, fpath ):
        with open(fpath, 'r') as f:
            return cls.from_str(iface_registry, f.read())

    @classmethod
    def from_data( cls, iface_registry, rec ):
        iface = iface_registry.resolve(rec.iface)
        public_key = PublicKey.from_der(rec.public_key_der)
        return cls(iface, public_key, rec.path, rec.routes)

    def __init__( self, iface, public_key, path, routes ):
        Url.__init__(self, iface, public_key, path)
        assert routes is None or is_list_list_inst(routes, str), repr(routes)
        self.routes = routes

    def to_data( self ):
        return self.type(self.iface.iface_id, self.public_key.to_der(), self.path, self.routes)

    def save_to_file( self, fpath ):
        with open(fpath, 'w') as f:
            r.write(self.to_str())
