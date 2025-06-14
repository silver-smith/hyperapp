
def resolve_fn_cfg_item(piece):
    return (None, piece)


def resolve_fn_cfg_value(piece, key, service, service_name):
    system_fn_creg = system.resolve_service('system_fn_creg')
    return system_fn_creg.animate(piece.system_fn)
