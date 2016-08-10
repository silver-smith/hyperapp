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
    intColumnType,
    dateTimeColumnType,
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
        Column('id', intColumnType),
        Column('created_at', dateTimeColumnType),
        ],
    commands=[
        ElementOpenCommand('open'),
        ElementCommand('delete'),
        OpenCommand('add'),
    ],
    key_column='id')

register_iface(blog_entry_iface)
register_iface(blog_iface)
