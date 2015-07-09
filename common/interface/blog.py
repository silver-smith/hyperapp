from . types import (
    tString,
    tInt,
    TDateTime,
    TOptional,
    TPath,
    Field,
    )
from . interface import RequestCmd, OpenCommand, Interface, register_iface
from . list import ElementCommand, ElementOpenCommand, ListInterface


blog_entry_iface = Interface('blog_entry',
                             content_fields=[Field('text', TOptional(tString))],
                             commands=[
                                 OpenCommand('parent'),
                                 OpenCommand('open_ref', [Field('ref_id', tString)]),
                                 RequestCmd('save', [Field('text', tString)], [Field('new_path', TPath())]),
                                 OpenCommand('refs'),
                                 ],
                             diff_type=tString)

blog_iface = ListInterface('blog',
                           columns=[tInt, TDateTime()],
                           commands=[
                               ElementOpenCommand('open'),
                               ElementCommand('delete'),
                               OpenCommand('add'),
                               ],
                            key_type=tInt)

register_iface(blog_entry_iface)
register_iface(blog_iface)
