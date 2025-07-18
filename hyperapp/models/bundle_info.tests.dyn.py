from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import bundle_info


@mark.fixture
def piece():
    capsule_list = [
        mosaic.put("Sample string"),
        mosaic.put(12345),
        ]
    return htypes.bundle_info.model(
        bundle_name="Sample bundle",
        roots=(capsule_list[0],),
        associations=(),
        capsules=tuple(capsule_list),
        )


def test_model(piece):
    info = bundle_info.bundle_info(piece)
    assert isinstance(info, htypes.bundle_info.bundle_info)


def test_open_root(piece):
    result = bundle_info.open_root(piece)
    assert isinstance(result, htypes.data_browser.record_view)


def test_open_capsules(piece):
    result = bundle_info.open_capsules(piece)
    assert isinstance(result, htypes.bundle_info.capsule_list_model)


@mark.fixture
def capsule_list_piece():
    return htypes.bundle_info.capsule_list_model(
        bundle_name="Sample bundle",
        capsules=(
            mosaic.put("Sample string"),
            mosaic.put(12345),
            ),
        )


def test_capsule_list(capsule_list_piece):
    items = bundle_info.capsule_list(capsule_list_piece)
    assert type(items) is list
    assert isinstance(items[0], htypes.bundle_info.capsule_item)


def test_open_capsule_item(capsule_list_piece):
    current_item = htypes.bundle_info.capsule_item(
        ref=mosaic.put("Sample string"),
        data_size=0,
        type_ref=pyobj_creg.actor_to_ref(htypes.builtin.string),
        type_str="<unused>",
        title="<unused>",
        )
    result = bundle_info.open_capsule(capsule_list_piece, current_item)
    assert isinstance(result, htypes.data_browser.record_view)


def test_open_associations(piece):
    result = bundle_info.open_associations(piece)
    assert isinstance(result, htypes.bundle_info.ass_list_model)


@mark.fixture
def ass_list_piece():
    return htypes.bundle_info.ass_list_model(
        bundle_name="Sample bundle",
        associations=(
            mosaic.put("Sample string"),
            mosaic.put(12345),
            ),
        )


def test_ass_list(ass_list_piece):
    items = bundle_info.ass_list(ass_list_piece)
    assert type(items) is list
    assert isinstance(items[0], htypes.bundle_info.capsule_item)


def test_open_ass_item(ass_list_piece):
    current_item = htypes.bundle_info.capsule_item(
        ref=mosaic.put("Sample string"),
        data_size=0,
        type_ref=pyobj_creg.actor_to_ref(htypes.builtin.string),
        type_str="<unused>",
        title="<unused>",
        )
    result = bundle_info.open_association(ass_list_piece, current_item)
    assert isinstance(result, htypes.data_browser.record_view)


def test_format_model(piece):
    title = bundle_info.format_model(piece)
    assert type(title) is str


def test_format_capsule_list_model(capsule_list_piece):
    title = bundle_info.format_capsule_list_model(capsule_list_piece)
    assert type(title) is str


def test_format_ass_list_model(ass_list_piece):
    title = bundle_info.format_ass_list_model(ass_list_piece)
    assert type(title) is str
