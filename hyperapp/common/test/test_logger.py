import pytest

from hyperapp.common.logger import log, set_log_storage



class StubStorage:

    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)


@pytest.fixture(autouse=True)
def storage():
    storage = StubStorage()
    set_log_storage(storage)
    return storage


def test_log_entry(storage):
    log.test_entry(foo='foo value', bar='bar value')
    assert storage.entries == [dict(
        name='test_entry',
        foo='foo value',
        bar='bar value',
        )]
