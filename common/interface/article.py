from . types import (
    TString,
    TInt,
    TOptional,
    TPath,
    TObject,
    Field,
    )
from . interface import (
    Command,
    OpenCommand,
    ElementCommand,
    ElementOpenCommand,
    Interface,
    ListInterface,
    register_iface,
    )


article_iface = Interface('article',
                          content_fields=[Field('text', TOptional(TString()))],
                          commands=[
                              Command('save', [Field('text', TString())], [Field('new_path', TPath())]),
                              OpenCommand('refs'),
                              ])

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
                                  content_fields=[
                                      Field('target', TObject()),
                                      ],
                                  commands=[
                                      OpenCommand('choose', [Field('target_path', TPath())]),
                                  ])

onwrap_object_selector_iface = Interface('article_unwrap_object_selector',
                                         content_fields=[Field('base', TObject())])


register_iface(article_iface)
register_iface(ref_list_iface)
register_iface(object_selector_iface)
register_iface(onwrap_object_selector_iface)
