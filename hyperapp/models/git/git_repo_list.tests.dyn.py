from pathlib import Path
from unittest.mock import Mock

import pygit2

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .tested.code import git_repo_list


def test_open():
    piece = git_repo_list.open_repo_list()
    assert piece


@mark.fixture
def data_dir():
    root = Path('/tmp/git-tests')
    repo_dir = root / 'phony-repo-1'
    if not repo_dir.exists():
        pygit2.init_repository(repo_dir)
    return root


@mark.fixture
def file_bundle_factory():
    storage = htypes.git.repo_list_storage(
        path_list=('/tmp/git-tests/phony-repo-1',),
        )
    file_bundle = Mock()
    file_bundle.load_piece.return_value = storage
    return file_bundle


@mark.fixture
def piece():
    return htypes.git.repo_list_model()


def test_model(piece):
    item_list = git_repo_list.repo_list_model(piece)
    assert type(item_list) is list
    assert item_list == [
        htypes.git.repo_item(
            name='phony-repo-1',
            path='/tmp/git-tests/phony-repo-1',
            current_branch='',  # Phony repo has no commits.
            ),
        ]


def test_add(piece):
    path = htypes.fs.path(
        parts=('tmp', 'git-tests', 'phony-repo-2'),
        )
    name = git_repo_list.add(piece, path)
    assert name == 'phony-repo-2'


def test_remove(piece):
    result = git_repo_list.remove(piece, current_key='phony-repo-1')
    assert result


def test_formatter(piece):
    title = git_repo_list.format_model(piece)
    assert type(title) is str
