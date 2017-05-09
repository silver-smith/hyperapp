import pytest
from hyperapp.client.list_object import ListDiff, Element, Slice, ListObject
from hyperapp.client.proxy_list_object import SliceAlgorithm


def make_slice(elements_range, bof=False):
    start, stop = elements_range
    elements = [Element(key=idx, order_key=idx, row=None, commands=[]) for idx in range(start, stop)]
    return Slice(sort_column_id='id', from_key=None, elements=elements, bof=bof, eof=False)

def slice2range(slice):
    return (slice.elements[0].key, slice.elements[-1].key + 1)


@pytest.mark.parametrize("slice_range, new_slice_range, expected_slice_range", [
    # existing, new, expected result
    ((0, 5), (0, 6), (0, 6)),
    ((0, 6), (0, 5), (0, 6)),
    ((0, 5), (1, 5), (0, 5)),
    ((1, 5), (0, 5), (0, 5)),
    ((0, 10), (5, 15), (0, 15)),
    ((5, 15), (0, 10), (0, 15)),
    ((0, 5), (4, 10), (0, 10)),
    ((4, 10), (0, 5), (0, 10)),
    ])
@pytest.mark.xfail
def test_intersecting_slices_should_be_properly_merged(slice_range, new_slice_range, expected_slice_range):
    slices = [make_slice(slice_range)]
    new_slice = make_slice(new_slice_range)
    SliceAlgorithm().merge_in_slice(slices, new_slice)
    assert len(slices) == 1
    assert expected_slice_range == slice2range(slices[0])

@pytest.mark.parametrize("slice_range, new_slice_range", [
    ((0, 5), (10, 15)),
    ((0, 5), (6, 10)),  # adjacent
    ((10, 15), (0, 5)),
    ((6, 10), (0, 5)),  # adjacent
    ])
def test_nonintersecting_slices_should_be_added(slice_range, new_slice_range):
    slices = [make_slice(slice_range)]
    new_slice = make_slice(new_slice_range)
    SliceAlgorithm().merge_in_slice(slices, new_slice)
    assert 2 == len(slices)


def test_pick_slice_with_empty_key_should_return_bof_slice():
    slices = [make_slice((20, 30), bof=False),
              make_slice((0, 10), bof=True),
              make_slice((10, 20), bof=False)]
    result = SliceAlgorithm().pick_slice(slices, sort_column_id='id', from_key=None, desc_count=0, asc_count=10)
    assert slices[1] == result

@pytest.mark.parametrize("slices_range, from_key, desc_count, asc_count, expected_slice_range", [
    ([(0, 10), (20, 30), (40, 50)], 25, 0, 10, (26, 30)),
    ([(0, 10), (20, 30), (40, 50)], 0, 0, 10, (1, 10)),
    ([(0, 10), (20, 30), (40, 50)], 48, 0, 10, (49, 50)),
    ([(0, 10), (20, 30), (40, 50)], 25, 1, 10, (25, 30)),
    ([(0, 10), (20, 30), (40, 50)], 0, 10, 10, (0, 10)),
    ([(0, 10), (20, 30), (40, 50)], 48, 5, 10, (44, 50)),
    ])
def test_pick_slice_should_return_proper_elements(slices_range, from_key, desc_count, asc_count, expected_slice_range):
    slices = list(map(make_slice, slices_range))
    result = SliceAlgorithm().pick_slice(slices, sort_column_id='id', from_key=from_key, desc_count=desc_count, asc_count=asc_count)
    assert expected_slice_range == slice2range(result)
