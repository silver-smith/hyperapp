from pathlib import Path
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .tested.code import wiki_pages


def test_open():
    piece = wiki_pages.open_wiki_pages()
    assert isinstance(piece, htypes.wiki_pages.list_model)


@mark.fixture
def data_dir():
    return Path('/tmp/wiki-pages-tests')


@mark.fixture
def file_bundle_factory():
    ref_1_piece = htypes.wiki_pages_tests.sample_model()
    storage = htypes.wiki_pages.storage(
        folders=(
            htypes.wiki_pages.folder(
                id='folder_1',
                parent_id=None,
                name="Folder 1",
                ),
            htypes.wiki_pages.folder(
                id='folder_2',
                parent_id=None,
                name="Folder 2",
                ),
            ),
        pages=(
            htypes.wiki_pages.page(
                id='page_1',
                parent_id=None,
                title="Page 1",
                wiki=htypes.wiki.wiki(
                    text="Page 1 text",
                    refs=(
                        htypes.wiki.wiki_ref('1', mosaic.put(ref_1_piece)),
                        ),
                    ),
                ),
            ),
        )
    file_bundle = Mock()
    file_bundle.load_piece.return_value = storage
    return file_bundle


@mark.fixture
def root_model():
    return htypes.wiki_pages.list_model(parent_id=None, folder_path=())


@mark.fixture
def folder_2_model():
    return htypes.wiki_pages.list_model(parent_id='folder_2', folder_path=('Folder 2',))


def test_root_list_model(root_model):
    item_list = wiki_pages.page_list_model(root_model)
    assert type(item_list) is list
    assert item_list == [
        htypes.wiki_pages.item('folder_1', "Folder 1"),
        htypes.wiki_pages.item('folder_2', "Folder 2"),
        htypes.wiki_pages.item('page_1', "Page 1"),
        ]


def test_page_model():
    model = htypes.wiki_pages.page_model(
        id='page_1',
        )
    page = wiki_pages.page_model(model)
    assert isinstance(page, htypes.wiki_pages.page)


def test_open_folder_locally(root_model, folder_2_model):
    current_key = folder_2_model.parent_id
    piece = wiki_pages.open(root_model, current_key, request=None)
    assert piece == folder_2_model


def test_open_folder_remotely(generate_rsa_identity, root_model, folder_2_model):
    identity = generate_rsa_identity(fast=True)
    request = Mock(receiver_identity=identity)
    current_key = folder_2_model.parent_id
    piece = wiki_pages.open(root_model, current_key, request)
    assert isinstance(piece, htypes.model.remote_model)
    assert web.summon(piece.model) == folder_2_model


def test_open_parent_locally(root_model, folder_2_model):
    piece, key = wiki_pages.open_parent(folder_2_model, request=None)
    assert piece == root_model
    assert key == folder_2_model.parent_id


def test_open_parent_remotelly(generate_rsa_identity, root_model, folder_2_model):
    identity = generate_rsa_identity(fast=True)
    request = Mock(receiver_identity=identity)
    piece, key = wiki_pages.open_parent(folder_2_model, request)
    assert isinstance(piece, htypes.model.remote_model)
    assert web.summon(piece.model) == root_model
    assert key == folder_2_model.parent_id


def test_add_root_folder(root_model, file_bundle_factory):
    folder_id = wiki_pages.add_folder(root_model, "New folder")
    assert type(folder_id) is str
    file_bundle_factory.save_piece.assert_called_once()


def _test_add_ref(folder_2_model, file_bundle_factory):
    ref_2_piece = htypes.wiki_pages_tests.sample_model(id=456)
    ref_2 = mosaic.put(ref_2_piece)
    ref_id = wiki_pages.add_ref(folder_2_model, ref_2)
    assert type(ref_id) is str
    file_bundle_factory.save_piece.assert_called_once()


def test_remove_folder(root_model, file_bundle_factory):
    result = wiki_pages.remove(root_model, 'folder_1')
    assert result is True
    file_bundle_factory.save_piece.assert_called_once()


def test_formatter(folder_2_model):
    text = wiki_pages.format_model(folder_2_model)
    assert text == "Wiki Pages: /Folder 2/"
