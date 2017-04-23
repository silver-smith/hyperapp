import pytest
from hyperapp.client.list_object import ListDiff, Element, Slice, ListObject
from hyperapp.client.proxy_list_object import SliceAlgorithm


def make_slice( elements_range ):
    start, stop = elements_range
    elements = [Element(key=idx, order_key=idx, row=None, commands=[]) for idx in range(start, stop)]
    return Slice(sort_column_id='id', from_key=None, direction='asc', elements=elements, bof=True, eof=True)


@pytest.fixture(params=[
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
def intersecting_slices(request):
    existing, new, expected = request.param
    return (
        [make_slice(existing)],
        make_slice(new),
        [make_slice(expected)],
        )

@pytest.mark.xfail
def test_intersecting_slices_should_be_properly_merged(intersecting_slices):
    slices, new_slice, expected_slices = intersecting_slices
    SliceAlgorithm().merge_in_slice(slices, new_slice)
    assert slices == expected_slices


@pytest.fixture(params=[
    ((0, 5), (10, 15)),
    ((0, 5), (6, 10)),  # adjacent
    ((10, 15), (0, 5)),
    ((6, 10), (0, 5)),  # adjacent
    ])
def nonintersecting_slices(request):
    existing, new = request.param
    return (
        [make_slice(existing)],
        make_slice(new),
        )

def test_nonintersecting_slices_should_be_added(nonintersecting_slices):
    slices, new_slice = nonintersecting_slices
    SliceAlgorithm().merge_in_slice(slices, new_slice)
    assert len(slices) == 2
