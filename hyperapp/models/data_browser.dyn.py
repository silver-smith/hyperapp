from hyperapp.common.htypes import TPrimitive, TList, TOptional, TRecord, ref_t

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark


def _data_browser(data, t):
    if isinstance(t, TPrimitive):
        return htypes.data_browser.primitive_view(
            data=mosaic.put(data, t),
            )
    if isinstance(t, TRecord):
        return htypes.data_browser.record_view(
            data=mosaic.put(data, t),
            )
    if isinstance(t, TList) and t.element_t is ref_t:
        return htypes.data_browser.ref_list_view(
            data=mosaic.put(data, t),
            )
    if isinstance(t, TList):
        return htypes.data_browser.list_view(
            data=mosaic.put(data, t),
            )
    if isinstance(t, TOptional):
        if data is None:
            return htypes.data_browser.primitive_view(
                data=mosaic.put(None),
                )
        else:
            return _data_browser(data, t.base_t)
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


def browse_list(piece):
    data = web.summon(piece.data)
    return [
        htypes.data_browser.list_item(
            idx=idx,
            value=str(elt),
            )
        for idx, elt in enumerate(data)
        ]


def list_open(piece, current_item):
    data = web.summon(piece.data)
    value = data[current_item.idx]
    t = deduce_t(value)
    return _data_browser(value, t)


def browse_ref_list(piece):
    data = web.summon(piece.data)
    result = []
    for idx, elt_ref in enumerate(data):
        elt = web.summon(elt_ref)
        item = htypes.data_browser.ref_list_item(
            idx=idx,
            type=str(deduce_t(elt)),
            value=str(elt),
            )
        result.append(item)
    return result


def ref_list_open(piece, current_item):
    data = web.summon(piece.data)
    value_ref = data[current_item.idx]
    value = web.summon(value_ref)
    t = deduce_t(value)
    return _data_browser(value, t)


@mark.model
def browse_primitive(piece):
    data = web.summon(piece.data)
    data_t = deduce_t(data)
    return htypes.data_browser.primitive_item(
        type=str(data_t),
        value=str(data),
        )


def browse_current_model(piece):
    t = deduce_t(piece)
    return _data_browser(piece, t)
