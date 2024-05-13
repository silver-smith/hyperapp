from hyperapp.common.htypes import TPrimitive, TRecord, ref_t

from . import htypes
from .services import (
    deduce_t,
    mark,
    mosaic,
    web,
    )


def _data_browser(data, t):
    if isinstance(t, TPrimitive):
        return htypes.data_browser.primitive_view(
            data=mosaic.put(data),
            )
    if isinstance(t, TRecord):
        return htypes.data_browser.record_view(
            data=mosaic.put(data),
            )
    raise RuntimeError(f"Data browser: Unsupported type: {t}: {data}")


def browse_record(piece):
    data = web.summon(piece.data)
    data_t = deduce_t(data)
    return [
        htypes.data_browser.record_item(
            name=name,
            type=str(t),
            value=str(getattr(data, name)),
            )
        for name, t in data_t.fields.items()
        ]


@mark.model
def browse_primitive(piece):
    data = web.summon(piece.data)
    data_t = deduce_t(data)
    return htypes.data_browser.primitive_item(
        type=str(data_t),
        value=str(data),
        )


def record_open(piece, current_item):
    data = web.summon(piece.data)
    data_t = deduce_t(data)
    name = current_item.name
    field_t = data_t.fields[name]
    value = getattr(data, name)
    if field_t is ref_t:
        value = web.summon(value)
        field_t = deduce_t(value)
    return _data_browser(value, field_t)


def browse_current_model(piece):
    t = deduce_t(piece)
    return _data_browser(piece, t)
