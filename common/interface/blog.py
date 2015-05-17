from . interface import (
    TString,
    TInt,
    Arg,
    Command,
    Interface,
    register_iface,
    )


blog_iface = Interface('blog', [])

register_iface(blog_iface)
