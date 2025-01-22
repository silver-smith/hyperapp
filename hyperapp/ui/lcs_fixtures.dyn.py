from unittest.mock import Mock

from .code.mark import mark


@mark.fixture
def lcs():
    def mock_get(key, default=None):
        return default
    lcs = Mock()
    lcs.get = mock_get
    return lcs
