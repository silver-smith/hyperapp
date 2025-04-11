import base64
from unittest.mock import Mock, patch

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .tested.code import ref_list


def test_open():
    piece = ref_list.open_ref_list()
    assert isinstance(piece, htypes.ref_list.model)


ref_list_yaml_format = '''
  folders:
  - id: folder_1
    parent_id: null
    name: Folder 1
  - id: folder_2
    parent_id: null
    name: Folder 2
  refs:
  - id: ref_1
    parent_id: null
    ref:
      hash_algorithm: {ref_1_hash_algorithm}
      hash: {ref_1_hash}
'''


def format_sample_model(piece):
    return f'sample-model({piece.id})'


@mark.config_fixture('formatter_creg')
def formatter_creg_config():
    return {
        htypes.ref_list_tests.sample_model: format_sample_model,
        }


@mark.fixture
def root_model():
    return htypes.ref_list.model(parent_id=None, folder_path=())


@mark.fixture
def folder_2_model():
    return htypes.ref_list.model(parent_id='folder_2', folder_path=('Folder 2',))


@mark.fixture
def mock_storage_path():
    ref_1_piece = htypes.ref_list_tests.sample_model(id=123)
    ref_1 = mosaic.put(ref_1_piece)
    ref_list_yaml_text = ref_list_yaml_format.format(
        ref_1_hash_algorithm=ref_1.hash_algorithm,
        ref_1_hash=base64.b64encode(ref_1.hash).decode('ascii'),
        )
    path = Mock()
    path.read_bytes.return_value = ref_list_yaml_text.encode()
    return path


def test_root_model(root_model, mock_storage_path):
    with patch.object(ref_list, '_STORAGE_PATH', mock_storage_path):
        item_list = ref_list.ref_list_model(root_model)
    assert type(item_list) is list
    assert item_list == [
        htypes.ref_list.item('folder_1', 'Folder 1'),
        htypes.ref_list.item('folder_2', 'Folder 2'),
        htypes.ref_list.item('ref_1', 'sample-model(123)'),
        ]


def test_open_folder(root_model, folder_2_model, mock_storage_path):
    with patch.object(ref_list, '_STORAGE_PATH', mock_storage_path):
        current_key = folder_2_model.parent_id
        piece = ref_list.open(root_model, current_key)
    assert piece == folder_2_model


def test_open_parent(root_model, folder_2_model, mock_storage_path):
    with patch.object(ref_list, '_STORAGE_PATH', mock_storage_path):
        piece, key = ref_list.open_parent(folder_2_model)
    assert piece == root_model
    assert key == folder_2_model.parent_id


def test_add_root_folder(root_model, mock_storage_path):
    with patch.object(ref_list, '_STORAGE_PATH', mock_storage_path):
        piece, folder_id = ref_list.add_folder(root_model, 'New folder')
    assert piece == root_model
    assert type(folder_id) is str
    mock_storage_path.write_bytes.assert_called_once()


def test_formatter(folder_2_model):
    text = ref_list.format_model(folder_2_model)
    assert text == "Ref list: /Folder 2/"
