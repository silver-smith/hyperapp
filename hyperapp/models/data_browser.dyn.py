from hyperapp.common.htypes import TRecord
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    mosaic,
    types,
    web,
    )


def deduce_t(data):
    return deduce_complex_value_type(mosaic, types, data)


def browse(piece):
    data = web.summon(piece.data)
    data_t = deduce_t(data)
    if isinstance(data_t, TRecord):
        return [
            htypes.data_browser.item(
                name=name,
                type=str(t),
                value=str(getattr(data, name)),
                )
            for name, t in data_t.fields.items()
            ]
    raise RuntimeError(f"Browser: Unsupported type: {data_t}: {data}")


def browse_current_model(piece):
    return htypes.data_browser.data_browser(
        data=mosaic.put(piece),
        )
