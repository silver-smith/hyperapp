from . interface import (
    TString,
    TInt,
    TPath,
    Field,
    Command,
    Interface,
    register_iface,
    )


article_iface = Interface('article', [
    Command('save', [Field('text', TString())], [Field('new_path', TPath())]),
    ])

ref_list_iface = Interface('article_ref_list', [
    Command('parent'),
    Command('add', [Field('target_path', TPath())]),
    ])

object_selector_iface = Interface('article_object_selector', [
    Command('choose', [Field('target_path', TPath())]),
    ])

onwrap_object_selector_iface = Interface('article_unwrap_object_selector', [])


register_iface(article_iface)
register_iface(ref_list_iface)
register_iface(object_selector_iface)
register_iface(onwrap_object_selector_iface)
