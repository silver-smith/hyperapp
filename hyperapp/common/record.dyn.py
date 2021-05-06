from hyperapp.common.htypes import (
    field_mt,
    record_mt,
    name_wrapped_mt,
    request_mt,
    interface_mt,
    )


def make_record_ref(mosaic, record_field_list):
    field_list = [
        field_mt(field.id, field.type_ref)
        for field in record_field_list
        ]
    record = record_mt(None, field_list)
    record_ref = mosaic.put(record)
    return mosaic.put(name_wrapped_mt('record_service_record', record_ref))


def record_t(mosaic, types, record_field_list):
    record_ref = make_record_ref(mosaic, record_field_list)
    return types.resolve(record_ref)


def record_interface_ref(mosaic, record_field_list):
    record_ref = make_record_ref(mosaic, record_field_list)
    record_field = field_mt('record', record_ref)
    get_method_ref = mosaic.put(request_mt('get', [], [record_field]))
    interface_ref = mosaic.put(interface_mt(None, [get_method_ref]))
    named_interface_ref = mosaic.put(name_wrapped_mt('record_service_interface', interface_ref))
    return named_interface_ref
