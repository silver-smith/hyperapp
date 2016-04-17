from hyperapp.common.identity import Identity


class IdentityController(object):

    def __init__( self ):
        self.identities = []  # (name, Identity) list

    def generate( self, name ):
        identity = Identity.generate()
        self.identities.append((name, identity))


identity_controller = IdentityController()
