from hyperapp.common.identity import Identity


class IdentityItem(object):

    def __init__( self, name, identity ):
        assert isinstance(name, basestring), repr(name)
        assert isinstance(identity, Identity), repr(identity)
        self.name = name
        self.identity = identity


class IdentityController(object):

    def __init__( self ):
        self._items = []  # (name, Identity) list

    def get_items( self ):
        return self._items

    def generate( self, name ):
        identity = Identity.generate()
        self._items.append(IdentityItem(name, identity))


identity_controller = IdentityController()
