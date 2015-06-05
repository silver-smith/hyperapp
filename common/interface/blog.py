from . interface import (
    TString,
    TInt,
    TDateTime,
    TPath,
    Field,
    Command,
    OpenCommand,
    ElementCommand,
    ElementOpenCommand,
    Interface,
    ListInterface,
    register_iface,
    )


blog_entry_iface = Interface('blog_entry',
                             content_fields=[Field('text', TString())],
                             commands=[
                                 Command('parent'),
                                 Command('open_ref', [Field('ref_id', TString())]),
                                 Command('save', [Field('text', TString())], [Field('new_path', TPath())]),
                                 OpenCommand('refs'),
                                 ])

blog_iface = ListInterface('blog',
                           columns=[TInt(), TDateTime()],
                           commands=[
                               ElementOpenCommand('open'),
                               ElementCommand('delete'),
                               Command('add'),
                               ],
                            key_type=TInt())

register_iface(blog_entry_iface)
register_iface(blog_iface)
