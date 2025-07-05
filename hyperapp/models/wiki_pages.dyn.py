import itertools
import logging
import uuid
from collections import defaultdict, namedtuple

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.value_diff import SetValueDiff

log = logging.getLogger(__name__)

_STORAGE_PATH = 'wiki_pages.cdr'


class WikiPages:

    def __init__(self, file_bundle):
        self._file_bundle = file_bundle
        self._folders = {}
        self._pages = {}
        self._folder_has_names = defaultdict(set)
        self._folder_title_to_id = {}

    def load(self):
        try:
            storage = self._file_bundle.load_piece()
        except FileNotFoundError:
            return
        self._folders = {folder.id: folder for folder in storage.folders}
        self._pages = {ref.id: ref for ref in storage.pages}
        for folder in self._folders.values():
            self._folder_has_names[folder.parent_id].add(folder.name)
        for page in self._pages.values():
            self._folder_title_to_id[page.parent_id, page.title] = page.id

    def _save(self):
        storage = htypes.wiki_pages.storage(
            folders=tuple(self._folders.values()),
            pages=tuple(self._pages.values()),
            )
        self._file_bundle.save_piece(storage)

    def enum_items(self, format, parent_id=None):
        for folder in self._folders.values():
            if folder.parent_id != parent_id:
                continue
            yield htypes.wiki_pages.item(
                id=folder.id,
                title=folder.name,
                )
        for page in self._pages.values():
            if page.parent_id != parent_id:
                continue
            yield htypes.wiki_pages.item(
                id=page.id,
                title=page.title,
                )

    def get_folder(self, item_id):
        return self._folders[item_id]

    def get_page(self, item_id):
        return self._pages[item_id]

    def get_folder_path(self, item_id):
        path = ()
        while item_id:
            folder = self._folders[item_id]
            path = (*path, folder.name)
            item_id = folder.parent_id
        return path

    def remove(self, item_id):
        try:
            folder = self._folders[item_id]
            del self._folders[item_id]
            self._folder_has_names[folder.parent_id].remove(folder.name)
        except KeyError:
            page = self._pages[item_id]
            del self._pages[item_id]
            del self._folder_title_to_id[page.parent_id, page.title]
        self._save()

    def append_folder(self, parent_id, name):
        if name in self._folder_has_names[parent_id]:
            log.warning("Folder with name %r already exists", name)
            return None
        folder = htypes.wiki_pages.folder_rec(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            name=name,
            )
        self._folders[folder.id] = folder
        self._folder_has_names[parent_id].add(name)
        self._save()
        return folder.id

    def save_page(self, parent_id, page_id, title, wiki):
        prev_title_id = self._folder_title_to_id.get((parent_id, title))
        if prev_title_id and prev_title_id != page_id:
            log.warning("Page with title %r already exists it this folder", title)
            return None
        if not page_id:
            page_id = str(uuid.uuid4())
        page = htypes.wiki_pages.page_rec(
            id=page_id,
            parent_id=parent_id,
            title=title,
            wiki=wiki,
            )
        self._pages[page_id] = page
        self._folder_title_to_id[parent_id, title] = page_id
        self._save()
        log.info("Saved page %s at folder %s", page_id, parent_id)
        return page_id


@mark.service
def wiki_pages(file_bundle_factory, data_dir):
    file_bundle = file_bundle_factory(data_dir / _STORAGE_PATH, encoding='cdr')
    pages = WikiPages(file_bundle)
    pages.load()
    return pages


@mark.model(key='id')
def page_list_model(piece, format, wiki_pages):
    return list(wiki_pages.enum_items(format, piece.parent_id))


@mark.model
def page_model(piece, wiki_pages):
    if piece.page_id:
        rec = wiki_pages.get_page(piece.page_id)
        return htypes.wiki_pages.page(
            title=rec.title,
            wiki=rec.wiki,
            )
    return htypes.wiki_pages.page(
        title=piece.title,
        wiki=htypes.wiki.wiki(
            text="",
            refs=(),
            ),
        )


@mark.model
def ref_list_model(piece, wiki_pages):
    if piece.page_id:
        rec = wiki_pages.get_page(piece.page_id)
        return rec.wiki.refs
    return []


@mark.command(preserve_remote=True)
def open(piece, current_key, wiki_pages):
    try:
        folder = wiki_pages.get_folder(item_id=current_key)
    except KeyError:
        return _open_page(wiki_pages, page_id=current_key)
    else:
        return _open_folder(wiki_pages, folder)


def _open_folder(wiki_pages, folder):
    path = wiki_pages.get_folder_path(folder.id)
    return htypes.wiki_pages.list_model(
        parent_id=folder.id,
        folder_path=tuple(path),
        )


def _open_page(wiki_pages, page_id):
    rec = wiki_pages.get_page(page_id)
    return htypes.wiki_pages.page_model(
        parent_id=rec.parent_id,
        page_id=rec.id,
        title=rec.title,
        )


@mark.command(preserve_remote=True)
def open_parent(piece, wiki_pages):
    if not piece.parent_id:
        return
    folder = wiki_pages.get_folder(piece.parent_id)
    piece = htypes.wiki_pages.list_model(
        parent_id=folder.parent_id,
        folder_path=piece.folder_path[:-1],
        )
    return (piece, folder.id)


@mark.command.add(args=['name'])
def add_folder(piece, name, wiki_pages):
    if not name:
        return
    folder_id = wiki_pages.append_folder(piece.parent_id, name)
    return folder_id


@mark.command(preserve_remote=True)
def new_page(piece, wiki_pages):
    return htypes.wiki_pages.page_model(
        parent_id=piece.parent_id,
        page_id=None,
        title="New wiki page",
        )


@mark.command(preserve_remote=True)
def save_page(piece, value, wiki_pages):
    page_id = wiki_pages.save_page(piece.parent_id, piece.page_id, value.title, value.wiki)
    path = wiki_pages.get_folder_path(piece.parent_id)
    model = htypes.wiki_pages.list_model(
        parent_id=piece.parent_id,
        folder_path=path,
        )
    return (model, page_id)


@mark.command(args=['ref'])
async def add_ref(piece, value, ref, wiki_pages, feed_factory):
    feed = feed_factory(piece)
    used_ids = {ref.id for ref in value.wiki.refs}
    for idx in itertools.count(1):
        ref_id = str(idx)
        if ref_id not in used_ids:
            break
    new_ref = htypes.wiki.wiki_ref(
        id=ref_id,
        target=ref,
        )
    new_value = htypes.wiki_pages.page(
        title=value.title,
        wiki=htypes.wiki.wiki(
            text=value.wiki.text,
            refs=(*value.wiki.refs, new_ref),
            ),
        )
    await feed.send(SetValueDiff(new_value))


@mark.command(preserve_remote=True)
def open_ref_list(piece):
    return htypes.wiki_pages.ref_list_model(
        parent_id=piece.parent_id,
        page_id=piece.page_id,
        )


@mark.command.remove
def remove(piece, current_id, wiki_pages):
    wiki_pages.remove(current_id)
    return True


@mark.global_command
def open_wiki_pages():
    return htypes.wiki_pages.list_model(parent_id=None, folder_path=())


@mark.actor.formatter_creg
def format_page_list_model(piece):
    path = "/"
    for name in piece.folder_path:
        path += name + "/"
    return f"Wiki Pages: {path}"


@mark.actor.formatter_creg
def format_page_model(piece):
    return f"Wiki page: {piece.title}"


@mark.actor.formatter_creg
def format_ref_list_model(piece, wiki_pages):
    if piece.page_id:
        rec = wiki_pages.get_page(piece.page_id)
        return f"Wiki page refs: {rec.title}"
    else:
        return "Wiki page refs: New page"
