import logging
import uuid
from collections import defaultdict, namedtuple

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)

_STORAGE_PATH = 'wiki_pages.cdr'


class WikiPages:

    def __init__(self, file_bundle):
        self._file_bundle = file_bundle
        self._folders = {}
        self._pages = {}
        self._folder_has_names = defaultdict(set)
        self._folder_has_titles = defaultdict(set)

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
            self._folder_has_titles[page.parent_id].add(page.title)

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
                name=folder.name,
                )
        for page in self._pages.values():
            if page.parent_id != parent_id:
                continue
            yield htypes.wiki_pages.item(
                id=page.id,
                name=page.title,
                )

    def get_folder(self, item_id):
        return self._folders[item_id]

    def get_page(self, item_id):
        return self._pages[item_id]

    def remove(self, item_id):
        try:
            folder = self._folders[item_id]
            del self._folders[item_id]
            self._folder_has_names[folder.parent_id].remove(folder.name)
        except KeyError:
            page = self._pages[item_id]
            del self._pages[item_id]
            self._folder_has_titles[page.parent_id].remove(page.title)
        self._save()

    def append_folder(self, parent_id, name):
        if name in self._folder_has_names[parent_id]:
            log.warning("Folder with name %r already exists", name)
            return None
        folder = htypes.wiki_pages.folder(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            name=name,
            )
        self._folders[folder.id] = folder
        self._folder_has_names[parent_id].add(name)
        self._save()
        return folder.id

    def append_page(self, parent_id, title, wiki):
        if title in self._folder_has_titles[parent_id]:
            log.warning("Page with title %r already exists", title)
            return None
        page = htypes.wiki_pages.page(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            title=title,
            wiki=wiki,
            )
        self._pages[page.id] = page
        self._folder_has_titles[parent_id].add(page.title)
        self._save()
        return page.id


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
    if piece.id:
        return wiki_pages.get_page(piece.id)
    return htypes.wiki_pages.page(
        id=str(uuid.uuid4()),
        parent_id=piece.parent_id,
        title="New wiki page",
        wiki=htypes.wiki.wiki(
            text="",
            refs=(),
            ),
        )


@mark.command
def open(piece, current_key, request, wiki_pages):
    try:
        folder = wiki_pages.get_folder(current_key)
        path = [folder.name]
        while folder.parent_id:
            folder = wiki_pages.get_folder(folder.parent_id)
            path = [folder.name, *path]
        piece = htypes.wiki_pages.list_model(
            parent_id=current_key,
            folder_path=tuple(path),
            )
        if request:
            piece = htypes.model.remote_model(
                model=mosaic.put(piece),
                remote_peer=mosaic.put(request.receiver_identity.peer.piece),
                )
        return piece
    except KeyError:
        ref = wiki_pages.get_ref(current_key)
        return web.summon(ref.ref)


@mark.command
def open_parent(piece, request, wiki_pages):
    if not piece.parent_id:
        return
    folder = wiki_pages.get_folder(piece.parent_id)
    piece = htypes.wiki_pages.list_model(
        parent_id=folder.parent_id,
        folder_path=piece.folder_path[:-1],
        )
    if request:
        piece = htypes.model.remote_model(
            model=mosaic.put(piece),
            remote_peer=mosaic.put(request.receiver_identity.peer.piece),
            )
    return (piece, folder.id)


@mark.command.add(args=['name'])
def add_folder(piece, name, wiki_pages):
    if not name:
        return
    folder_id = wiki_pages.append_folder(piece.parent_id, name)
    return folder_id


@mark.command
def new_page(piece, wiki_pages):
    return htypes.wiki_pages.page_model(
        parent_id=piece.parent_id,
        id=None,
        )


@mark.command.remove
def remove(piece, current_id, wiki_pages):
    wiki_pages.remove(current_id)
    return True


@mark.global_command
def open_wiki_pages():
    return htypes.wiki_pages.list_model(parent_id=None, folder_path=())


@mark.actor.formatter_creg
def format_model(piece):
    path = "/"
    for name in piece.folder_path:
        path += name + "/"
    return f"Wiki Pages: {path}"
