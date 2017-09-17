import pytest
from hyperapp.common.list_object import Element, Chunk, ListDiff
from hyperapp.client.list_object import ListObject
from hyperapp.client.proxy_list_object import ChunkAlgorithm
from hyperapp.client.slice import Slice


def rangel(*args):
    return list(range(*args))

def element(key):
    return Element(key=key, order_key=key, row=None)

def chunk(from_key, keys, bof=False, eof=False):
    elements = [element(key) for key in keys]
    return Chunk(sort_column_id='id', from_key=from_key, elements=elements, bof=bof, eof=eof)

def slice(keys, bof=False, eof=False):
    return Slice(sort_column_id='id', bof=bof, eof=eof, keys=list(keys))


@pytest.mark.parametrize('slice, new_chunk, expected_new_slice', [
    (slice([0, 1, 2, 3]), chunk(3, [4, 5]), slice([0, 1, 2, 3, 4, 5])),
    (slice([0, 1, 2, 3, 4, 5]), chunk(1, [11, 12]), slice([0, 1, 11, 12])),  # old elements after from_key must be thrown away
    (slice([10, 11, 12]), chunk(None, [1, 2, 3], bof=True), slice([1, 2, 3], bof=True)),  # bof chunk must replace all
    (slice([1]), chunk(1, [2, 3], eof=True), slice([1, 2, 3], eof=True)),  # eof must be recorded in slice
    (slice([1], eof=True), chunk(1, [2, 3], eof=False), slice([1, 2, 3], eof=False)),  # eof must be recorded in slice
    ])
def test_new_chunk_should_be_properly_merged_in(slice, new_chunk, expected_new_slice):
    slice.add_fetched_chunk(new_chunk)
    assert slice == expected_new_slice


@pytest.mark.parametrize('slice, diff, expected_new_slice', [
    (slice([1, 2, 4, 5]), ListDiff.add_one(element(3)), slice([1, 2, 3, 4, 5])),  # between existing ones
    (slice([2, 3, 4, 5]), ListDiff.add_one(element(1)), slice([2, 3, 4, 5])),  # before first one and not bof - ignore
    (slice([2, 3, 4, 5], bof=True), ListDiff.add_one(element(1)), slice([1, 2, 3, 4, 5])),  # before first one and bof - insert
    (slice([1, 2, 3, 4]), ListDiff.add_one(element(5)), slice([1, 2, 3, 4])),  # after last one and not eof - ignore
    (slice([1, 2, 3, 4], eof=True), ListDiff.add_one(element(5)), slice([1, 2, 3, 4, 5])),  # after last one and eof - append
    ])
def test_diff_should_be_properly_merged_in(slice, diff, expected_new_slice):
    slice.merge_in_diff(diff)
    assert slice == expected_new_slice


# @pytest.mark.parametrize('slice, key, desc_count, asc_count, expected_chunk', [
#     (slice(rangel(0, 10), bof=False), None, 0, 10, None),  # request with key=None means we want bof
#     (slice(rangel(0, 10), bof=True), None, 0, 10, chunk(None, rangel(0, 10), bof=True)),  # request with key=None means we want bof
#     ])
# def test_pick_chunk_should_return_proper_chunk(slice, key, desc_count, asc_count, expected_chunk):
#     chunk = slice.pick_chunk(key, desc_count, asc_count)
#     assert chunk == expected_chunk


# def test_pick_chunk_with_empty_key_should_return_bof_chunk():
#     chunks = [make_chunk((20, 30), bof=False),
#               make_chunk((0, 10), bof=True),
#               make_chunk((10, 20), bof=False)]
#     result = ChunkAlgorithm().pick_chunk(chunks, sort_column_id='id', from_key=None, desc_count=0, asc_count=10)
#     assert chunks[1] == result

# @pytest.mark.parametrize('chunks_range, from_key, desc_count, asc_count, expected_chunk_range', [
#     ([(0, 10), (20, 30), (40, 50)], 25, 0, 10, (26, 30)),
#     ([(0, 10), (20, 30), (40, 50)], 0, 0, 10, (1, 10)),
#     ([(0, 10), (20, 30), (40, 50)], 48, 0, 10, (49, 50)),
#     ([(0, 10), (20, 30), (40, 50)], 25, 1, 10, (25, 30)),
#     ([(0, 10), (20, 30), (40, 50)], 0, 10, 10, (0, 10)),
#     ([(0, 10), (20, 30), (40, 50)], 48, 5, 10, (44, 50)),
#     ])
# def test_pick_chunk_should_return_proper_elements(chunks_range, from_key, desc_count, asc_count, expected_chunk_range):
#     chunks = list(map(make_chunk, chunks_range))
#     result = ChunkAlgorithm().pick_chunk(chunks, sort_column_id='id', from_key=from_key, desc_count=desc_count, asc_count=asc_count)
#     assert expected_chunk_range == chunk2range(result)
