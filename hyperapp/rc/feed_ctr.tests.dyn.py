from . import htypes
from .services import (
    local_types,
    mosaic,
    pyobj_creg,
    )
from .tested.code import feed_ctr


def test_construct_list_feed():
    module_res = htypes.builtin.python_module(
        module_name='feed_ctr_tests',
        source='',
        file_path='/feed_ctr_tests.dyn.py',
        import_list=(),
        )
    string_res = pyobj_creg.actor_to_piece(htypes.builtin.string)
    name_to_res = {}
    feed_piece_t = htypes.feed_ctr_tests.sample_feed
    feed_piece_t_res = pyobj_creg.actor_to_piece(feed_piece_t)
    element_t = htypes.feed_ctr_tests.sample_item
    element_t_res = pyobj_creg.actor_to_piece(element_t)
    feed_ctr.construct_list_feed(
        piece=htypes.rc_constructors.list_feed_ctr(
            t=mosaic.put(feed_piece_t_res),
            element_t=mosaic.put(element_t_res),
            ),
        custom_types=local_types,
        name_to_res=name_to_res,
        module_res=module_res,
        )
    assert 'feed_ctr_tests_sample_feed.list_feed' in name_to_res


def test_construct_index_tree_feed():
    module_res = htypes.builtin.python_module(
        module_name='feed_ctr_tests',
        source='',
        file_path='/feed_ctr_tests.dyn.py',
        import_list=(),
        )
    string_res = pyobj_creg.actor_to_piece(htypes.builtin.string)
    name_to_res = {}
    feed_piece_t = htypes.feed_ctr_tests.sample_feed
    feed_piece_t_res = pyobj_creg.actor_to_piece(feed_piece_t)
    element_t = htypes.feed_ctr_tests.sample_item
    element_t_res = pyobj_creg.actor_to_piece(element_t)
    feed_ctr.construct_index_tree_feed(
        piece=htypes.rc_constructors.index_tree_feed_ctr(
            t=mosaic.put(feed_piece_t_res),
            element_t=mosaic.put(element_t_res),
            ),
        custom_types=local_types,
        name_to_res=name_to_res,
        module_res=module_res,
        )
    assert 'feed_ctr_tests_sample_feed.index_tree_feed' in name_to_res
