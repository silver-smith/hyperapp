
class ViewRegistry(object):

    def __init__( self ):
        self.registry = {}  # view id -> Handle ctr

    def register( self, view_id, handle_ctr ):
        assert view_id not in self.registry, repr(view_id)  # Duplicate id
        self.registry[view_id] = handle_ctr

    def resolve( self, contents ):
        return self.registry[contents.view_id](contents)


view_registry = ViewRegistry()
