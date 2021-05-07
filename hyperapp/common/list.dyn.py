from hyperapp.common.htypes import (
    list_mt,
    field_mt,
    record_mt,
    request_mt,
    interface_mt,
    name_wrapped_mt,
    )


def list_row_ref(mosaic, list_ot):
    field_list = [
        field_mt(column.id, column.type_ref)
        for column in list_ot.column_list
        ]
    row_mt = record_mt(None, field_list)
    row_ref = mosaic.put(row_mt)
    named_row_ref = mosaic.put(name_wrapped_mt('list_service_row', row_ref))
    return named_row_ref


def list_row_t(mosaic, types, list_ot):
    named_row_ref = list_row_ref(mosaic, list_ot)
    return types.resolve(named_row_ref)


def list_interface_ref(mosaic, list_ot):
    named_row_ref = list_row_ref(mosaic, list_ot)
    row_list_ref = mosaic.put(list_mt(named_row_ref))
    rows_field = field_mt('rows', row_list_ref)
    get_method_ref = mosaic.put(request_mt('get', [], [rows_field]))
    interface_ref = mosaic.put(interface_mt(None, [get_method_ref]))
    named_interface_ref = mosaic.put(name_wrapped_mt('list_service_interface', interface_ref))
    return named_interface_ref
