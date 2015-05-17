from . interface import (
    TString,
    TInt,
    Arg,
    Command,
    Interface,
    register_iface,
    )


blog_entry_iface = Interface('blog_entry', [
    Command('save', [Arg('text', TString())]),
    ])

blog_iface = Interface('blog', [])

register_iface(blog_entry_iface)
register_iface(blog_iface)
