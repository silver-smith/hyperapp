from . import htypes
from .services import (
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
    adapter = htypes.record_field_adapter.record_field_adapter(
        record_adapter=None,
        field_name=k.field_name,
        )
