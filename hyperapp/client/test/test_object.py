from unittest.mock import Mock, MagicMock, patch
from hyperapp.client.object import ObjectObserver, Object


def test_object_observers():
    observer_1 = ObjectObserver()
    observer_2 = ObjectObserver()
    observer_1.object_changed = MagicMock()
    observer_2.object_changed = MagicMock()
    object = Object()
    object.observers_gone = MagicMock()
    object.subscribe(observer_1, 1, key=11)
    object.subscribe(observer_2, 2, key=22)
    object._notify_object_changed()
    observer_1.object_changed.assert_called_once_with(1, key=11)
    observer_2.object_changed.assert_called_once_with(2, key=22)
    del observer_1
    object.observers_gone.assert_not_called()
    del observer_2
    object.observers_gone.assert_called_once_with()
