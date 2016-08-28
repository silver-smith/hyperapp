from ..htypes import (
    tString,
    tInt,
    tDateTime,
    TOptional,
    Field,
    RequestCmd,
    OpenCommand,
    Interface,
    register_iface,
    Column,
    ElementCommand,
    ElementOpenCommand,
    ListInterface,
    )
from .article import article_iface


blog_entry_iface = Interface('blog_entry', base=article_iface,
                             commands=[
                                 OpenCommand('parent'),
                                 ])

blog_iface = ListInterface(
    'blog',
    columns=[
        Column('id', tInt, is_key=True),
        Column('created_at', tDateTime),
        ],
    commands=[
        ElementOpenCommand('open'),
        ElementCommand('delete'),
        OpenCommand('add'),
    ])

register_iface(blog_entry_iface)
register_iface(blog_iface)
