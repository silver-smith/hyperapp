import os
import textwrap

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark


@mark.global_command
async def open_sample_static_text():
    return "Sample text"


@mark.global_command
async def open_sample_wiki_text():
    text = textwrap.dedent("""
        Sample wiki text
        ~~~~~~~~~~~~~~~~

        * This is reference to a `Static text <1>`_.
        * And this one is to a `Static list <2>`_.
        * Here is `Sample tree model <3>`_.
        """)
    ref_items = tuple([
        htypes.sample_list.item(1, "First", "First list item for wiki sample"),
        htypes.sample_list.item(2, "Second", "Second item"),
        htypes.sample_list.item(3, "Third", "Third item"),
        ])
    return htypes.wiki.wiki(
        text=text,
        refs=(
            htypes.wiki.wiki_ref('1', mosaic.put("Some static text for wiki sample")),
            htypes.wiki.wiki_ref('2', mosaic.put(ref_items)),
            htypes.wiki.wiki_ref('3', mosaic.put(htypes.sample_tree.model())),
            ),
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
