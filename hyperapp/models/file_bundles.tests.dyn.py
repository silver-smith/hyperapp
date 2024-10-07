from . import htypes
from .services import mosaic
from .code.mark import mark
from .tested.code import file_bundles


def test_open_list():
    piece = file_bundles.open_file_bundle_list()
    assert isinstance(piece, htypes.file_bundles.view)


def test_bundle_list():
    piece = htypes.file_bundles.view()
    item_list = file_bundles.file_bundle_list(piece)
    assert type(item_list) is list
    for item in item_list:
        assert isinstance(item, htypes.file_bundles.item)


class MockBundle:

    def load_ref(self, register_associations=False):
        root = htypes.file_bundles_tests.sample_root()
        return mosaic.put(root)

        
@mark.fixture
def file_bundle(path, encoding):
    return MockBundle()


def test_open_bundle():
    piece = htypes.file_bundles.view()
    current_item = htypes.file_bundles.item(
        name="<unused>",
        path="/tmp/non-existent.cdr",
        )
    result = file_bundles.open(piece, current_item)
    assert isinstance(result, htypes.data_browser.record_view)
