import weakref
from unittest.mock import Mock


class SampleObj:
    pass


def test_finalizer():
    obj_1 = SampleObj()
    obj_2 = SampleObj()
    obj_1_gone = Mock()
    obj_2_gone = Mock()
    weakref.finalize(obj_1, obj_1_gone)
    weakref.finalize(obj_2, obj_2_gone)
    del obj_1
    obj_1_gone.assert_called_once()
    obj_2_gone.assert_not_called()



def test_weakset_with_finalizer():
    obj_1 = SampleObj()
    obj_2 = SampleObj()
    obj_1_gone = Mock()
    obj_2_gone = Mock()
    weakref.finalize(obj_1, obj_1_gone)
    weakref.finalize(obj_2, obj_2_gone)
    ws = weakref.WeakSet({obj_1})
    ws.add(obj_2)
    assert len(ws) == 2
    del obj_1
    assert len(ws) == 1
    obj_1_gone.assert_called_once()
    obj_2_gone.assert_not_called()
    assert ws
    del obj_2
    assert len(ws) == 0
    assert not ws
    obj_2_gone.assert_called_once()
