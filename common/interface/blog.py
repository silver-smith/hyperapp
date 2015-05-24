from . interface import (
    TString,
    TInt,
    Field,
    Command,
    Interface,
    register_iface,
    )


blog_entry_iface = Interface('blog_entry', [
    Command('parent'),
    Command('open_ref', [Field('ref_id', TString())]),
    Command('save', [Field('text', TString())]),
    Command('refs'),
    ])

blog_iface = Interface('blog', [])

register_iface(blog_entry_iface)
register_iface(blog_iface)
