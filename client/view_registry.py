

_views = {}

def register_view( id, handle_ctr ):
    _views[id] = handle_ctr

def resolve_view( id ):
    return _views[id]
