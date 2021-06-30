from hyperapp.common.htypes import (
    list_mt,
    field_mt,
    record_mt,
    request_mt,
    interface_mt,
    name_wrapped_mt,
    )


def tree_item_ref(mosaic, column_list):
    field_list = [
        field_mt(column.id, column.type_ref)
        for column in column_list
        ]
    item_mt = record_mt(None, field_list)
    item_ref = mosaic.put(item_mt)
    named_item_ref = mosaic.put(name_wrapped_mt('tree_service_item', item_ref))
    return named_item_ref


def tree_item_t(mosaic, types, tree_service):
    named_item_ref = tree_item_ref(mosaic, tree_service.column_list)
    return types.resolve(named_item_ref)


def pick_key_column(tree_service):
    for column in tree_service.column_list:
        if column.id == tree_service.key_column_id:
            return column
    raise RuntimeError(f"Key column {tree_service.key_column_id} is missing from: {tree_service.column_list}")


def tree_interface_ref(mosaic, tree_service):
    key_column = pick_key_column(tree_service)
    path_type_ref = mosaic.put(list_mt(key_column.type_ref))
    path_field = field_mt('path', path_type_ref)
    
    named_item_ref = tree_item_ref(mosaic, tree_service.column_list)
    item_list_ref = mosaic.put(list_mt(named_item_ref))
    items_field = field_mt('items', item_list_ref)

    get_method_ref = mosaic.put(request_mt('get', [path_field], [items_field]))
    interface_ref = mosaic.put(interface_mt(None, [get_method_ref]))
    named_interface_ref = mosaic.put(name_wrapped_mt('tree_service_interface', interface_ref))
    return named_interface_ref
