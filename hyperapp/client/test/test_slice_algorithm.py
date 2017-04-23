from hyperapp.client.list_object import ListDiff, Element, Slice, ListObject
from hyperapp.client.proxy_list_object import SliceAlgorithm


def test_superset_should_be_properly_merged():
    existing_elements = [Element(key=idx, row=None, commands=[]) for idx in range(20)]
    slices = [Slice(sort_column_id='id', from_key=None, direction='asc', elements=existing_elements, bof=True, eof=True)]
    new_elements = [Element(key=idx, row=None, commands=[]) for idx in range(21)]
    new_slice = Slice(sort_column_id='id', from_key=None, direction='asc', elements=new_elements, bof=True, eof=True)
    SliceAlgorithm().merge_in_slice(slices, new_slice)
    assert len(slices) == 1
    expected_elements = [Element(key=idx, row=None, commands=[]) for idx in range(21)]
    expected_slice = [Slice(sort_column_id='id', from_key=None, direction='asc', elements=expected_elements, bof=True, eof=True)]
    assert slices[0] == expected_slice
