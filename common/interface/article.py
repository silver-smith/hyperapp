from . types import (
    TString,
    TInt,
    TOptional,
    TPath,
    Field,
    TRecord,
    )
from . interface import (
    tHandle,
    tObjHandle,
    TObject,
    Object,
    Command,
    OpenCommand,
    Interface,
    register_iface,
    )
from . list import ElementCommand, ElementOpenCommand, ListInterface


tObjSelectorHandle = tHandle.register('object_selector', fields=[
        Field('ref', TObject()),
        Field('target', tHandle),
        ])
ObjSelectorHandle = tObjSelectorHandle.instantiate

tObjSelectorUnwrapHandle = tHandle.register('object_selector_unwrap', fields=[
        Field('base_handle', tHandle),
        ])
ObjSelectorUnwrapHandle = tObjSelectorUnwrapHandle.instantiate

tTextViewHandle = tHandle.register('text_view', base=tObjHandle)
tTextEditHandle = tHandle.register('text_edit', base=tObjHandle)


article_iface = Interface('article',
                          content_fields=[Field('text', TOptional(TString()))],
                          commands=[
                              Command('save', [Field('text', TString())], [Field('new_path', TPath())]),
                              OpenCommand('refs'),
                              ],
                          diff_type=TString())

ref_list_iface = ListInterface('article_ref_list',
                               columns=[TInt(), TString()],
                               commands=[
                                   OpenCommand('parent'),
                                   OpenCommand('add', [Field('target_path', TPath())]),
                                   ElementOpenCommand('open'),
                                   ElementCommand('delete'),
                                   ],
                                key_type=TInt())

object_selector_iface = Interface('article_object_selector',
                                  commands=[
                                      OpenCommand('choose', [Field('target_path', TPath())]),
                                  ])

onwrap_object_selector_iface = Interface('article_unwrap_object_selector',
                                         content_fields=[Field('base', TObject())])


register_iface(article_iface)
register_iface(ref_list_iface)
register_iface(object_selector_iface)
register_iface(onwrap_object_selector_iface)
