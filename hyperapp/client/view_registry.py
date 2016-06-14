from ..common.htypes import tHandle
from .view import Handle


class ViewRegistry(object):

    def __init__( self ):
        self.registry = {}  # view id -> Handle ctr

    def register( self, view_id, handle_ctr ):
        assert view_id not in self.registry, repr(view_id)  # Duplicate id
        self.registry[view_id] = handle_ctr

    def is_view_registered( self, view_id ):
        return view_id in self.registry

    def resolve( self, contents, server=None ):
        assert isinstance(contents, tHandle), repr(contents)
        ctr = self.registry[contents.view_id]
        handle = ctr(contents, server)
        assert isinstance(handle, Handle), repr((contents.view_id, handle))  # view must resolve to handle
        return handle


view_registry = ViewRegistry()
