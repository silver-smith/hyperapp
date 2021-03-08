from unittest.mock import Mock, MagicMock, patch

import pytest

from hyperapp.common import cdr_coders  # register codec


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return [
        'async.ui.commander',
        'async.ui.object',
        ]


def test_object_observers(code):
    observer_1 = code.object.ObjectObserver()
    observer_2 = code.object.ObjectObserver()
    observer_1.object_changed = MagicMock()
    observer_2.object_changed = MagicMock()
    object = code.object.Object()
    object.observers_arrived = MagicMock()
    object.observers_gone = MagicMock()
    object.subscribe(observer_1, 1, key=11)
    object.observers_arrived.assert_called_once_with()
    object.observers_arrived.reset_mock()
    object.subscribe(observer_2, 2, key=22)
    object.observers_arrived.assert_not_called()
    object._notify_object_changed()
    observer_1.object_changed.assert_called_once_with(1, key=11)
    observer_2.object_changed.assert_called_once_with(2, key=22)
    del observer_1
    object.observers_gone.assert_not_called()
    del observer_2
    object.observers_gone.assert_called_once_with()
