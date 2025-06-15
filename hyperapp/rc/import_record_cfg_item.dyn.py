from .services import (
    web,
    )


def resolve_import_record_cfg_item(piece):
    key = (piece.module_name, piece.import_name)
    return (key, piece)


def resolve_import_record_cfg_value(piece, key, system, service_name):
    return web.summon(piece.resource)
