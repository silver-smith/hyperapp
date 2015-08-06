from . types import (
    tString,
    tInt,
    tDateTime,
    TOptional,
    tPath,
    Field,
    )
from . interface import RequestCmd, OpenCommand, Interface, register_iface
from . list import intColumnType, dateTimeColumnType, Column, ElementCommand, ElementOpenCommand, ListInterface
from . article import article_iface


blog_entry_iface = Interface('blog_entry', base=article_iface,
                             commands=[
                                 OpenCommand('parent'),
                                 ])

blog_iface = ListInterface(
    'blog',
    columns=[
        Column('id', 'Article id', intColumnType),
        Column('created_at', 'Creation date', dateTimeColumnType),
        ],
    commands=[
        ElementOpenCommand('open'),
        ElementCommand('delete'),
        OpenCommand('add'),
    ],
    key_column='id')

register_iface(blog_entry_iface)
register_iface(blog_iface)
