from ..htypes import (
    tString,
    tInt,
    TOptional,
    tUrl,
    tPath,
    Field,
    TRecord,
    tHandle,
    tViewHandle,
    tObject,
    RequestCmd,
    OpenCommand,
    Interface,
    register_iface,
    intColumnType,
    Column,
    ElementCommand,
    ElementOpenCommand,
    ListInterface,
    )


tObjSelectorHandle = tHandle.register('object_selector', base=tViewHandle, fields=[
        Field('ref', tObject),
        Field('target', tHandle),
        ])

tObjSelectorUnwrapHandle = tHandle.register('object_selector_unwrap', base=tViewHandle, fields=[
        Field('base_handle', tHandle),
        ])

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
        Column('url', 'Url'),
    ],
    commands=[
        OpenCommand('parent'),
        OpenCommand('add', [Field('target_url', tUrl)]),
        ElementOpenCommand('open'),
        ElementCommand('delete'),
    ],
    key_column='ref_id')

object_selector_iface = Interface('article_object_selector',
                                  commands=[
                                      OpenCommand('choose', [Field('target_url', tUrl)]),
                                  ])

onwrap_object_selector_iface = Interface('article_unwrap_object_selector',
                                         content_fields=[Field('base', tObject)])


register_iface(article_iface)
register_iface(ref_list_iface)
register_iface(object_selector_iface)
register_iface(onwrap_object_selector_iface)
