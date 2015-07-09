from . types import (
    tString,
    tInt,
    tDateTime,
    TOptional,
    tPath,
    Field,
    )
from . interface import RequestCmd, OpenCommand, Interface, register_iface
from . list import ElementCommand, ElementOpenCommand, ListInterface


blog_entry_iface = Interface('blog_entry',
                             content_fields=[Field('text', TOptional(tString))],
                             commands=[
                                 OpenCommand('parent'),
                                 OpenCommand('open_ref', [Field('ref_id', tString)]),
                                 RequestCmd('save', [Field('text', tString)], [Field('new_path', tPath)]),
                                 OpenCommand('refs'),
                                 ],
                             diff_type=tString)

blog_iface = ListInterface('blog',
                           columns=[tInt, tDateTime],
                           commands=[
                               ElementOpenCommand('open'),
                               ElementCommand('delete'),
                               OpenCommand('add'),
                               ],
                            key_type=tInt)

register_iface(blog_entry_iface)
register_iface(blog_iface)
