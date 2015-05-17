from . interface import (
    TString,
    TInt,
    TPath,
    Arg,
    Command,
    Interface,
    register_iface,
    )


ref_list_iface = Interface('article_ref_list', [
    Command('parent'),
    Command('add', [Arg('target_path', TPath())]),
    ])

object_selector_iface = Interface('article_object_selector', [
    Command('choose', [Arg('target_path', TPath())]),
    ])

onwrap_object_selector_iface = Interface('article_unwrap_object_selector', [])


register_iface(ref_list_iface)
register_iface(object_selector_iface)
register_iface(onwrap_object_selector_iface)
