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
    tObjHandle,
    tObject,
    Object,
    RequestCmd,
    OpenCommand,
    Interface,
    register_iface,
    )
from . list import ElementCommand, ElementOpenCommand, ListInterface


tTextViewHandle = tHandle.register('text_view', base=tObjHandle)
TextViewHandle = tTextViewHandle.instantiate

tTextEditHandle = tHandle.register('text_edit', base=tObjHandle)
TextEditHandle = tTextEditHandle.instantiate

tObjSelectorHandle = tHandle.register('object_selector', fields=[
        Field('ref', tObject),
        Field('target', tHandle),
        ])
ObjSelectorHandle = tObjSelectorHandle.instantiate

tObjSelectorUnwrapHandle = tHandle.register('object_selector_unwrap', fields=[
        Field('base_handle', tHandle),
        ])
ObjSelectorUnwrapHandle = tObjSelectorUnwrapHandle.instantiate


article_iface = Interface('article',
                          content_fields=[Field('text', TOptional(tString))],
                          commands=[
                              RequestCmd('save', [Field('text', tString)], [Field('new_path', tPath)]),
                              OpenCommand('refs'),
                              ],
                          diff_type=tString)

ref_list_iface = ListInterface('article_ref_list',
                               columns=[tInt, tString],
                               commands=[
                                   OpenCommand('parent'),
                                   OpenCommand('add', [Field('target_path', tPath)]),
                                   ElementOpenCommand('open'),
                                   ElementCommand('delete'),
                                   ],
                                key_type=tInt)

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
