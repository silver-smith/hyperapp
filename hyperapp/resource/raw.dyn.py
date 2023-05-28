from .services import (
    web,
    )


def python_object(piece):
    return web.summon(piece.resource)
