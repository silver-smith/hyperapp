from . interface import (
    TString,
    TInt,
    Arg,
    Command,
    Interface,
    register_iface,
    )


blog_entry_iface = Interface('blog_entry', [
    Command('parent'),
    Command('open_ref', [Arg('ref_id', TString())]),
    Command('save', [Arg('text', TString())]),
    Command('refs'),
    ])

blog_iface = Interface('blog', [])

register_iface(blog_entry_iface)
register_iface(blog_iface)
