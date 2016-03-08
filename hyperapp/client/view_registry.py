
class ViewRegistry(object):

    def __init__( self ):
        self.registry = {}  # view id -> Handle ctr

    def register( self, view_id, handle_ctr ):
        assert view_id not in self.registry, repr(view_id)  # Duplicate id
        self.registry[view_id] = handle_ctr

    def is_view_registered( self, view_id ):
        return view_id in self.registry

    def resolve( self, contents, server=None ):
        ctr = self.registry[contents.view_id]
        return ctr(contents, server)


view_registry = ViewRegistry()
