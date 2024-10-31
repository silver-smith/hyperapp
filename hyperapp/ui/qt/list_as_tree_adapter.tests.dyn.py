import asyncio
import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .tested.code import list_as_tree_adapter

log = logging.getLogger(__name__)


def sample_fn_1(piece):
    log.info("Sample fn 1: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_adapter_tests.sample_list_1), repr(piece)
    return [
        htypes.list_as_tree_adapter_tests.item_1(0, "one", "First item"),
        htypes.list_as_tree_adapter_tests.item_1(1, "two", "Second item"),
        htypes.list_as_tree_adapter_tests.item_1(2, "three", "Third item"),
        ]


def sample_fn_1_open(piece, current_item):
    log.info("Sample fn 1 open: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_adapter_tests.sample_list_1), repr(piece)
    return htypes.list_as_tree_adapter_tests.sample_list_2(base_id=current_item.id)


def sample_fn_2(piece):
    log.info("Sample fn 2: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_adapter_tests.sample_list_2), repr(piece)
    return [
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 0, "one"),
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 1, "two"),
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 2, "three"),
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 3, "four"),
        ]


def sample_fn_2_open(piece, current_item):
    log.info("Sample fn 2 open: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_adapter_tests.sample_list_2), repr(piece)
    return htypes.list_as_tree_adapter_tests.sample_list_3(base_id=current_item.id)


def sample_fn_3(piece):
    log.info("Sample fn 3: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_adapter_tests.sample_list_3), repr(piece)
    return [
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 0, "First item"),
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 1, "Second item"),
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 2, "Third item"),
        htypes.list_as_tree_adapter_tests.item_2(piece.base_id*10 + 3, "Fourth item"),
        ]


@mark.config_fixture('visualizer_reg')
def visualizer_config():
    fn_2 = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_fn_2),
        ctx_params=('piece',),
        service_params=(),
        )
    fn_3 = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_fn_3),
        ctx_params=('piece',),
        service_params=(),
        )
    item_t_2 = pyobj_creg.actor_to_piece(htypes.list_as_tree_adapter_tests.item_2)
    item_t_3 = pyobj_creg.actor_to_piece(htypes.list_as_tree_adapter_tests.item_3)
    ui_t_2 = htypes.model.list_ui_t(
        item_t=mosaic.put(item_t_2),
        )
    ui_t_3 = htypes.model.list_ui_t(
        item_t=mosaic.put(item_t_3),
        )
    return {
        htypes.list_as_tree_adapter_tests.sample_list_2: htypes.model.model(
            ui_t=mosaic.put(ui_t_2),
            system_fn=mosaic.put(fn_2),
            ),
        htypes.list_as_tree_adapter_tests.sample_list_3: htypes.model.model(
            ui_t=mosaic.put(ui_t_3),
            system_fn=mosaic.put(fn_3),
            ),
        }


class MockSubscriber:

    def __init__(self):
        self._queue = asyncio.Queue()

    def process_diff(self, diff):
        log.info("Mock subscriber: got diff: %s", diff)
        asyncio.create_task(self._queue.put(diff))

    async def wait(self, cond, timeout=5):
        async with asyncio.timeout(timeout):
            while not cond():
                log.info("Mock subscriber: condition not met, wait for next diff: %s", cond)
                await self._queue.get()
            log.info("Mock subscriber: condition is met: %s", cond)


@mark.config_fixture('model_command_reg')
def model_command_reg_config(partial_ref):
    open_fn_1 = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('piece', 'current_item'),
        service_params=(),
        unbound_fn=sample_fn_1_open,
        bound_fn=sample_fn_1_open,
        )
    open_fn_2 = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('piece', 'current_item'),
        service_params=(),
        unbound_fn=sample_fn_2_open,
        bound_fn=sample_fn_2_open,
        )
    command_1 = UnboundModelCommand(
        d=htypes.list_as_tree_adapter_tests.open_1_d(),
        ctx_fn=open_fn_1,
        properties=htypes.command.properties(False, False, False),
        )
    command_2 = UnboundModelCommand(
        d=htypes.list_as_tree_adapter_tests.open_2_d(),
        ctx_fn=open_fn_2,
        properties=htypes.command.properties(False, False, False),
        )
    return {
        htypes.list_as_tree_adapter_tests.sample_list_1: [command_1],
        htypes.list_as_tree_adapter_tests.sample_list_2: [command_2],
        }


async def test_three_layers(data_to_ref):
    ctx = Context()
    model = htypes.list_as_tree_adapter_tests.sample_list_1()
    root_item_t = pyobj_creg.actor_to_piece(htypes.list_as_tree_adapter_tests.item_1)
    open_command_1_d_ref = data_to_ref(htypes.list_as_tree_adapter_tests.open_1_d())
    open_command_2_d_ref = data_to_ref(htypes.list_as_tree_adapter_tests.open_2_d())
    piece_2_t = pyobj_creg.actor_to_piece(htypes.list_as_tree_adapter_tests.sample_list_2)
    piece_3_t = pyobj_creg.actor_to_piece(htypes.list_as_tree_adapter_tests.sample_list_3)
    fn_1 = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_fn_1),
        ctx_params=('piece',),
        service_params=(),
        )
    adapter_piece = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(fn_1),
        root_open_children_command_d=open_command_1_d_ref,
        layers=(
            htypes.list_as_tree_adapter.layer(
                piece_t=mosaic.put(piece_2_t),
                open_children_command_d=open_command_2_d_ref,
                ),
            htypes.list_as_tree_adapter.layer(
                piece_t=mosaic.put(piece_3_t),
                open_children_command_d=None,
                ),
            ),
        )

    adapter = list_as_tree_adapter.ListAsTreeAdapter.from_piece(adapter_piece, model, ctx)
    subscriber = MockSubscriber()
    adapter.subscribe(subscriber)

    assert adapter.column_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'name'
    assert adapter.column_title(2) == 'text'

    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 1
    assert adapter.cell_data(row_1_id, 1) == "two"
    assert adapter.cell_data(row_1_id, 2) == "Second item"

    assert adapter.row_count(row_1_id) == 0

    await subscriber.wait(lambda: adapter.row_count(row_1_id) == 4)
    row_1_2_id = adapter.row_id(row_1_id, 2)
    assert adapter.cell_data(row_1_2_id, 0) == 12
    assert adapter.cell_data(row_1_2_id, 1) == "three"

    row_2_id = adapter.row_id(0, 2)
    await subscriber.wait(lambda: adapter.row_count(row_2_id) == 4)
    row_2_3_id = adapter.row_id(row_2_id, 3)
    assert adapter.cell_data(row_2_3_id, 0) == 23
    assert adapter.cell_data(row_2_3_id, 1) == "four"

    await subscriber.wait(lambda: adapter.has_children(row_2_3_id))

    await subscriber.wait(lambda: adapter.has_children(row_1_2_id))
    row_1_2_0_id = adapter.row_id(row_1_2_id, 0)
    assert adapter.cell_data(row_1_2_0_id, 0) == 120
    assert adapter.cell_data(row_1_2_0_id, 1) == "First item"
    assert not adapter.has_children(row_1_2_0_id)

    assert adapter.get_item_piece([]) == model
    assert adapter.get_item_piece([1]) == htypes.list_as_tree_adapter_tests.sample_list_2(1)
    assert adapter.get_item_piece([1, 2]) == htypes.list_as_tree_adapter_tests.sample_list_3(12)


async def test_single_layer():
    ctx = Context()
    model = htypes.list_as_tree_adapter_tests.sample_list_1()
    root_item_t = pyobj_creg.actor_to_piece(htypes.list_as_tree_adapter_tests.item_1)
    fn_1 = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_fn_1),
        ctx_params=('piece',),
        service_params=(),
        )
    adapter_piece = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(fn_1),
        root_open_children_command_d=None,
        layers=(),
        )
    adapter = list_as_tree_adapter.ListAsTreeAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'name'
    assert adapter.column_title(2) == 'text'

    assert adapter.has_children(0)
    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 1
    assert adapter.cell_data(row_1_id, 1) == "two"
    assert adapter.cell_data(row_1_id, 2) == "Second item"

    assert not adapter.has_children(adapter.row_id(0, 0))
    assert not adapter.has_children(adapter.row_id(0, 1))
    assert not adapter.has_children(adapter.row_id(0, 2))
