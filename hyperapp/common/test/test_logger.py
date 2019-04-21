from contextlib import contextmanager

import pytest

from hyperapp.common.logger import log, logger_inited



class StubStorage:

    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def close(self):
        pass


@pytest.fixture
def init():

    @contextmanager
    def inited():
        storage = StubStorage()
        with logger_inited(storage):
            yield storage

    return inited


def test_entry(init):
    with init() as storage:
        log.test_entry(foo='foo-value', bar='bar-value')
    assert storage.entries == [dict(
        type='entry',
        name='test_entry',
        foo='foo-value',
        bar='bar-value',
        )]


def test_context(init):
    with init() as storage:
        with log.test_context(foo='foo-value'):
            log.test_entry(bar='bar-value')
    assert storage.entries == [
        dict(type='context-enter', name='test_context', foo='foo-value'),
        dict(type='entry', name='test_entry', bar='bar-value'),
        dict(type='context-exit', name='test_context'),
        ]


def test_nested_context(init):
    with init() as storage:
        with log.root_context(foo='foo'):
            log.foo_entry(bar='bar')
            with log.nested_context(bar='bar'):
                log.inner_entry(foo='foo')
    assert storage.entries == [
        dict(type='context-enter', name='root_context', foo='foo'),
        dict(type='entry', name='foo_entry', bar='bar'),
        dict(type='context-enter', name='nested_context', bar='bar'),
        dict(type='entry', name='inner_entry', foo='foo'),
        dict(type='context-exit', name='nested_context'),
        dict(type='context-exit', name='root_context'),
        ]
