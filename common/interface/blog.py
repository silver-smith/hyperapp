from . interface import (
    TString,
    TInt,
    TPath,
    Field,
    Command,
    ElementCommand,
    Interface,
    ListInterface,
    register_iface,
    )


blog_entry_iface = Interface('blog_entry', [
    Command('parent'),
    Command('open_ref', [Field('ref_id', TString())]),
    Command('save', [Field('text', TString())], [Field('new_path', TPath())]),
    Command('refs'),
    ])

blog_iface = ListInterface('blog', [
    ElementCommand('open'),
    Command('add'),
    ])

register_iface(blog_entry_iface)
register_iface(blog_iface)
