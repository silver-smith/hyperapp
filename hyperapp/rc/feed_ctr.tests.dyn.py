from . import htypes
from .services import (
    local_types,
    mosaic,
    pyobj_creg,
    )
from .tested.code import feed_ctr


def test_construct_feed():
    module_res = htypes.builtin.python_module(
        module_name='feed_ctr_tests',
        source='',
        file_path='/feed_ctr_tests.dyn.py',
        import_list=(),
        )
    string_res = pyobj_creg.reverse_resolve(htypes.builtin.string)
    name_to_res = {}
    feed_ctr.construct_list_feed(
        piece=htypes.rc_constructors.list_feed_ctr(
            element_t=mosaic.put(string_res),
            ),
        custom_types=local_types,
        name_to_res=name_to_res,
        module_res=module_res,
        )
    assert 'builtin_string.list_feed' in name_to_res
