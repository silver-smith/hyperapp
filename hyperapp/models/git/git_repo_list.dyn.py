import logging
from pathlib import Path

import pygit2

from . import htypes
from .code.mark import mark

log = logging.getLogger(__name__)

_STORAGE_PATH = 'git_repo_list.json'


class RepoList:

    def __init__(self, file_bundle):
        self._file_bundle = file_bundle
        self._name_to_path = {}

    def load(self):
        try:
            storage = self._file_bundle.load_piece()
        except FileNotFoundError:
            return
        for path_str in storage.path_list:
            path = Path(path_str)
            self._name_to_path[path.name] = path

    def _save(self):
        storage = htypes.git.repo_list_storage(
            path_list=tuple(str(p) for p in self._name_to_path.values()),
            )
        self._file_bundle.save_piece(storage)

    def enum_items(self):
        for name, path in self._name_to_path.items():
            repo = pygit2.Repository(path)
            try:
                current_branch = repo.head.shorthand
            except pygit2.GitError:
                current_branch = ''
            yield htypes.git.repo_item(
                name=name,
                path=str(path),
                current_branch=current_branch,
                )

    def add(self, path):
        self._name_to_path[path.name] = path
        self._save()
        return path.name

    def remove(self, name):
        del self._name_to_path[name]
        self._save()


@mark.service
def repo_list(file_bundle_factory, data_dir):
    file_bundle = file_bundle_factory(data_dir / _STORAGE_PATH, encoding='json')
    repo_list = RepoList(file_bundle)
    repo_list.load()
    return repo_list


@mark.model(key='name')
def repo_list_model(piece, repo_list):
    return list(repo_list.enum_items())


@mark.command.add(args=['path'])
def add(piece, path, repo_list):
    if not path:
        return
    repo_name = repo_list.add(Path('/', *path.parts))
    return repo_name


@mark.command.remove
def remove(piece, current_key, repo_list):
    if not current_key:
        return
    repo_list.remove(current_key)
    return True


@mark.global_command
def open_repo_list():
    return htypes.git.repo_list_model()


@mark.actor.formatter_creg
def format_model(piece):
    return "Git repositories"
