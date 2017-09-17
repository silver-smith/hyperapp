import pytest
from hyperapp.common.list_object import Element, Chunk, ListDiff
from hyperapp.client.list_object import ListObject
from hyperapp.client.proxy_list_object import ChunkAlgorithm


def make_chunk(elements_range, bof=False):
    start, stop = elements_range
    elements = [Element(key=idx, order_key=idx, row=None, commands=[]) for idx in range(start, stop)]
    return Chunk(sort_column_id='id', from_key=None, elements=elements, bof=bof, eof=False)

def chunk2range(chunk):
    return (chunk.elements[0].key, chunk.elements[-1].key + 1)


@pytest.mark.parametrize("chunk_range, new_chunk_range, expected_chunk_range", [
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
def test_intersecting_chunks_should_be_properly_merged(chunk_range, new_chunk_range, expected_chunk_range):
    chunks = [make_chunk(chunk_range)]
    new_chunk = make_chunk(new_chunk_range)
    ChunkAlgorithm().merge_in_chunk(chunks, new_chunk)
    assert len(chunks) == 1
    assert expected_chunk_range == chunk2range(chunks[0])

@pytest.mark.parametrize("chunk_range, new_chunk_range", [
    ((0, 5), (10, 15)),
    ((0, 5), (6, 10)),  # adjacent
    ((10, 15), (0, 5)),
    ((6, 10), (0, 5)),  # adjacent
    ])
def test_nonintersecting_chunks_should_be_added(chunk_range, new_chunk_range):
    chunks = [make_chunk(chunk_range)]
    new_chunk = make_chunk(new_chunk_range)
    ChunkAlgorithm().merge_in_chunk(chunks, new_chunk)
    assert 2 == len(chunks)


def test_pick_chunk_with_empty_key_should_return_bof_chunk():
    chunks = [make_chunk((20, 30), bof=False),
              make_chunk((0, 10), bof=True),
              make_chunk((10, 20), bof=False)]
    result = ChunkAlgorithm().pick_chunk(chunks, sort_column_id='id', from_key=None, desc_count=0, asc_count=10)
    assert chunks[1] == result

@pytest.mark.parametrize("chunks_range, from_key, desc_count, asc_count, expected_chunk_range", [
    ([(0, 10), (20, 30), (40, 50)], 25, 0, 10, (26, 30)),
    ([(0, 10), (20, 30), (40, 50)], 0, 0, 10, (1, 10)),
    ([(0, 10), (20, 30), (40, 50)], 48, 0, 10, (49, 50)),
    ([(0, 10), (20, 30), (40, 50)], 25, 1, 10, (25, 30)),
    ([(0, 10), (20, 30), (40, 50)], 0, 10, 10, (0, 10)),
    ([(0, 10), (20, 30), (40, 50)], 48, 5, 10, (44, 50)),
    ])
def test_pick_chunk_should_return_proper_elements(chunks_range, from_key, desc_count, asc_count, expected_chunk_range):
    chunks = list(map(make_chunk, chunks_range))
    result = ChunkAlgorithm().pick_chunk(chunks, sort_column_id='id', from_key=from_key, desc_count=desc_count, asc_count=asc_count)
    assert expected_chunk_range == chunk2range(result)
