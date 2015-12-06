import pickle
from . identity import PublicKey


class Endpoint(object):

    @classmethod
    def load_from_file( cls, fpath ):
        with open(fpath, 'rb') as f:
            public_key_pem, routes = pickle.load(f)
        return cls(PublicKey.from_pem(public_key_pem), routes)

    def __init__( self, public_key, routes ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        self.public_key = public_key
        self.routes = routes

    def save_to_file( self, fpath ):
        with open(fpath, 'wb') as f:
            pickle.dump((self.public_key.to_pem(), self.routes), f)

    def __repr__( self ):
        return 'Endpoint(%s)' % self.public_key.to_pem().splitlines()[1]
