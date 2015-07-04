from . types import (
    TString,
    TInt,
    TOptional,
    TPath,
    Field,
    TRecord,
    )
from . interface import (
    Handle,
    ObjHandle,
    TObject,
    Object,
    Command,
    OpenCommand,
    Interface,
    register_iface,
    )
from . list import ElementCommand, ElementOpenCommand, ListInterface


class ObjSelectorHandle(Handle):

    my_type = TRecord([
        Field('ref', TObject()),
        Field('target', Handle.type),
        ])

    def __init__( self, ref, target ):
        assert isinstance(ref, Object), repr(ref)
        assert target is None or isinstance(target, Handle), repr(target)
        Handle.__init__(self, 'object_selector')
        self.ref = ref
        self.target = target


class ObjSelectorUnwrap(Handle):

    my_type = TRecord([
        Field('base_handle', Handle.type),
        ])

    def __init__( self, base_handle ):
        Handle.__init__(self, 'object_selector_unwrap')
        self.base_handle = base_handle


ObjHandle.register('text_view')
ObjHandle.register('text_edit')
ObjSelectorHandle.register('object_selector')
ObjSelectorUnwrap.register('object_selector_unwrap')


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
