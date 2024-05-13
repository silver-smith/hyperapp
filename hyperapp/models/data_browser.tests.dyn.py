from . import htypes
from .services import (
    mosaic,
    web,
    )
from .tested.code import data_browser


def test_browse_current_model_record():
    piece_1 = htypes.data_browser_tests.sample_model_1()
    result_1 = data_browser.browse_current_model(piece_1)
    assert isinstance(result_1, htypes.data_browser.record_view)
    piece_2 = htypes.data_browser_tests.sample_model_2()
    result_2 = data_browser.browse_current_model(piece_2)
    assert isinstance(result_2, htypes.data_browser.record_view)


def test_browse_record():
    data = htypes.data_browser_tests.sample_data(
        name="Sample name",
        sample_list=(11, 22, 33),
        inner=htypes.data_browser_tests.inner_data("Sample inner text"),
        value=mosaic.put("Sample value"),
        )
    piece = htypes.data_browser.record_view(
        data=mosaic.put(data),
        )
    result = data_browser.browse_record(piece)
    assert len(result) == 4
    assert isinstance(result[0], htypes.data_browser.record_item)
    assert result[0].name == 'name'
    assert result[0].type == 'str'
    assert result[0].value == data.name
    assert result[1].name == 'sample_list'


def test_browse_list():
    elt_1 = "Sample element 1"
    elt_2 = "Sample element 2"
    data = (elt_1, elt_2)
    piece = data_browser.browse_current_model(data)
    assert isinstance(piece, htypes.data_browser.list_view)
    result = data_browser.browse_list(piece)
    assert type(result) is list
    assert len(result) == 2
    assert isinstance(result[0], htypes.data_browser.list_item)
    assert result[0].idx == 0
    assert result[0].value == elt_1
    assert result[1].idx == 1
    assert result[1].value == str(elt_2)

    current_item = result[1]
    view = data_browser.list_open(piece, current_item)
    assert isinstance(view, htypes.data_browser.primitive_view)
    assert web.summon(view.data) == elt_2


def test_browse_ref_list():
    elt_1 = "Sample element 1"
    elt_2 = 12345
    data = (mosaic.put(elt_1), mosaic.put(elt_2))
    piece = data_browser.browse_current_model(data)
    assert isinstance(piece, htypes.data_browser.ref_list_view)
    result = data_browser.browse_ref_list(piece)
    assert type(result) is list
    assert len(result) == 2
    assert isinstance(result[0], htypes.data_browser.ref_list_item)
    assert result[0].idx == 0
    assert result[0].type == 'str'
    assert result[0].value == elt_1
    assert result[1].idx == 1
    assert result[1].type == 'int'
    assert result[1].value == str(elt_2)

    current_item = result[1]
    view = data_browser.ref_list_open(piece, current_item)
    assert isinstance(view, htypes.data_browser.primitive_view)
    assert web.summon(view.data) == elt_2


def test_browse_primitive():
    data = "Sample primitive string"
    piece = data_browser.browse_current_model(data)
    assert isinstance(piece, htypes.data_browser.primitive_view)
    result = data_browser.browse_primitive(piece)
    assert isinstance(result, htypes.data_browser.primitive_item)
    assert result.type == 'str'
    assert result.value == data


def test_browse_primitive_string_opt():
    field = "Sample primitive string"
    data = htypes.data_browser_tests.sample_opt_data(
        str_field=field,
        )
    piece = htypes.data_browser.record_view(mosaic.put(data))
    current_item = htypes.data_browser.record_item(
        name="str_field",
        type="",
        value="",
        )
    view = data_browser.record_open(piece, current_item)
    assert isinstance(view, htypes.data_browser.primitive_view)
    assert web.summon(view.data) == field


def test_browse_primitive_string_opt_none():
    data = htypes.data_browser_tests.sample_opt_data(
        str_field=None,
        )
    piece = htypes.data_browser.record_view(mosaic.put(data))
    current_item = htypes.data_browser.record_item(
        name="str_field",
        type="",
        value="",
        )
    view = data_browser.record_open(piece, current_item)
    assert isinstance(view, htypes.data_browser.primitive_view)
    assert web.summon(view.data) == None


def test_record_open():
    data = htypes.data_browser_tests.sample_data(
        name="Sample name",
        sample_list=(11, 22, 33),
        inner=htypes.data_browser_tests.inner_data("Sample inner text"),
        value=mosaic.put("Sample value"),
        )
    piece = htypes.data_browser.record_view(
        data=mosaic.put(data),
        )
    current_item = htypes.data_browser.record_item(
        name="inner",
        type="",
        value="",
        )
    result = data_browser.record_open(piece, current_item)
    assert isinstance(result, htypes.data_browser.record_view)
    assert web.summon(result.data) == data.inner


def test_record_open_ref():
    data_1 = htypes.data_browser_tests.sample_data(
        name="Sample name 1",
        sample_list=(11, 22,),
        inner=htypes.data_browser_tests.inner_data("Sample inner text"),
        value=mosaic.put("Sample value"),
        )
    data_2 = htypes.data_browser_tests.sample_data(
        name="Sample name 2",
        sample_list=(22, 33),
        inner=htypes.data_browser_tests.inner_data("Sample inner text"),
        value=mosaic.put(data_1),
        )
    piece = htypes.data_browser.record_view(
        data=mosaic.put(data_2),
        )
    current_item = htypes.data_browser.record_item(
        name="value",
        type="",
        value="",
        )
    result = data_browser.record_open(piece, current_item)
    assert isinstance(result, htypes.data_browser.record_view)
    assert web.summon(result.data) == data_1
