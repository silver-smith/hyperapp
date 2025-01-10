from hyperapp.boot.htypes import TPrimitive, TList, TOptional, TRecord, ref_t

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark


def data_browser(data, t=None):
    if t is None:
        t = deduce_t(data)
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
            return data_browser(data, t.base_t)
    raise RuntimeError(f"Data browser: Unsupported type: {t}: {data}")


@mark.model
def browse_record(piece):
    data, data_t = web.summon_with_t(piece.data)
    return [
        htypes.data_browser.record_item(
            name=name,
            type=str(t),
            value=str(getattr(data, name)),
            )
        for name, t in data_t.fields.items()
        ]


@mark.command
def record_open(piece, current_item):
    data, data_t = web.summon_with_t(piece.data)
    name = current_item.name
    field_t = data_t.fields[name]
    value = getattr(data, name)
    if field_t is ref_t:
        value, field_t = web.summon_with_t(value)
    return data_browser(value, field_t)


@mark.model
def browse_list(piece):
    data, data_t = web.summon_with_t(piece.data)
    return [
        htypes.data_browser.list_item(
            idx=idx,
            type=str(data_t.element_t),
            value=str(elt),
            )
        for idx, elt in enumerate(data)
        ]


@mark.command
def list_open(piece, current_item):
    data, data_t = web.summon_with_t(piece.data)
    value = data[current_item.idx]
    return data_browser(value, data_t.element_t)


@mark.model
def browse_ref_list(piece):
    data = web.summon(piece.data)
    result = []
    for idx, elt_ref in enumerate(data):
        elt, t = web.summon_with_t(elt_ref)
        item = htypes.data_browser.ref_list_item(
            idx=idx,
            type=str(t),
            value=str(elt),
            )
        result.append(item)
    return result


@mark.command
def ref_list_open(piece, current_item):
    data = web.summon(piece.data)
    value_ref = data[current_item.idx]
    value, t = web.summon_with_t(value_ref)
    return data_browser(value, t)


@mark.model
def browse_primitive(piece):
    data, data_t = web.summon_with_t(piece.data)
    return htypes.data_browser.primitive_item(
        type=str(data_t),
        value=str(data),
        )


@mark.global_command
def browse_current_model(piece):
    return data_browser(piece)
