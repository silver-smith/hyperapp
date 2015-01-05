
_id2iface = {}


def register_iface( id, obj_ctr ):
    _id2iface[id] = obj_ctr

def resolve_iface( id ):
    return _id2iface[id]

