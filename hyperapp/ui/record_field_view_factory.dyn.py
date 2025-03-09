from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


def record_field_list(piece):
    record_t = pyobj_creg.invite(piece.record_t)
    k_list = []
    for name in record_t.fields:
        k = htypes.record_field_view_factory.factory_k(
            field_name=name,
            )
        k_list.append(k)
    return k_list


def record_field_get(k):
    record_adapter = htypes.crud.record_adapter()
    adapter = htypes.record_field_adapter.record_field_adapter(
        record_adapter=mosaic.put(record_adapter),
        field_name=k.field_name,
        )
    return htypes.line_edit.edit_view(
        adapter=mosaic.put(adapter),
        )
