from . types import (
    tString,
    tInt,
    TOptional,
    tPath,
    Field,
    TRecord,
    )
from . interface import (
    tHandle,
    tSimpleHandle,
    tObject,
    Object,
    RequestCmd,
    OpenCommand,
    Interface,
    register_iface,
    )
from . list import intColumnType, Column, ElementCommand, ElementOpenCommand, ListInterface


tObjSelectorHandle = tHandle.register('object_selector', base=tSimpleHandle, fields=[
        Field('ref', tObject),
        Field('target', tHandle),
        ])
ObjSelectorHandle = tObjSelectorHandle.instantiate

tObjSelectorUnwrapHandle = tHandle.register('object_selector_unwrap', base=tSimpleHandle, fields=[
        Field('base_handle', tHandle),
        ])
ObjSelectorUnwrapHandle = tObjSelectorUnwrapHandle.instantiate


article_iface = Interface('article',
                          content_fields=[Field('text', TOptional(tString))],
                          commands=[
                              RequestCmd('save', [Field('text', tString)], [Field('new_path', tPath)]),
                              OpenCommand('refs'),
                              OpenCommand('open_ref', [Field('ref_id', tString)]),
                              ],
                          diff_type=tString)

ref_list_iface = ListInterface(
    'article_ref_list',
    columns=[
        Column('ref_id', 'Id', intColumnType),
        Column('path', 'Path'),
    ],
    commands=[
        OpenCommand('parent'),
        OpenCommand('add', [Field('target_path', tPath)]),
        ElementOpenCommand('open'),
        ElementCommand('delete'),
    ],
    key_column='ref_id')

object_selector_iface = Interface('article_object_selector',
                                  commands=[
                                      OpenCommand('choose', [Field('target_path', tPath)]),
                                  ])

onwrap_object_selector_iface = Interface('article_unwrap_object_selector',
                                         content_fields=[Field('base', tObject)])


register_iface(article_iface)
register_iface(ref_list_iface)
register_iface(object_selector_iface)
register_iface(onwrap_object_selector_iface)
