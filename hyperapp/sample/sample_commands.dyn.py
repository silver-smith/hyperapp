import os
import textwrap

from . import htypes
from .code.mark import mark


@mark.global_command
async def open_sample_static_text():
    return "Sample text"


@mark.global_command
async def open_sample_wiki_text():
    text = textwrap.dedent("""
        Sample wiki text
        This is `ref#1 <1>`_.
        And this is `ref#2 <2>`_.
        """)
    return htypes.wiki.wiki(
        text=text,
        refs=(),
        )


@mark.global_command
async def open_sample_static_list():
    items = [
        htypes.sample_list.item(1, "First", "First item"),
        htypes.sample_list.item(2, "Second", "Second item"),
        htypes.sample_list.item(3, "Third", "Third item"),
        ]
    return items


@mark.global_command
async def show_state(model_state):
    return str(model_state)


@mark.command
async def details(piece, current_idx):
    return f"{piece} current idx: {current_idx}"


@mark.command
async def sample_tree_info(piece):
    return f"Sample tree piece: {piece}"


@mark.global_command
def system_info():
    uname = os.uname()
    info = {
        'user': os.getlogin(),
        'nodename': uname.nodename,
        'version': uname.version,
        'cpu_count': str(os.cpu_count()),
        }
    return [
        htypes.sample_commands.system_info_item(idx, key, value)
        for idx, (key, value) in enumerate(info.items())
        ]
