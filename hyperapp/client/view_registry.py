from ..common.htypes import tHandle
from .view import View


class ViewRegistry(object):

    def __init__( self ):
        self.registry = {}  # view id -> Handle ctr

    def register( self, view_id, handle_ctr ):
        assert view_id not in self.registry, repr(view_id)  # Duplicate id
        self.registry[view_id] = handle_ctr

    def is_view_registered( self, view_id ):
        return view_id in self.registry

    def resolve( self, parent, state ):
        assert isinstance(state, tHandle), repr(state)
        ctr = self.registry[state.view_id]
        view = ctr(parent, state)
        assert isinstance(view, View), repr((state.view_id, view))  # must resolve to View
        return view


view_registry = ViewRegistry()
