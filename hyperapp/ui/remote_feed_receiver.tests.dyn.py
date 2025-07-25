from unittest.mock import Mock

from . import htypes
from .code.mark import mark
from .code.list_diff import IndexListDiff
from .tested.code import remote_feed_receiver as remote_feed_receiver_module


# Remove dep cycle: feed -> feed_servant -> remote_feed_receiver -> feed.
@mark.fixture
def feed_factory(model):
    return Mock()


def test_remote_feed_receiver(generate_rsa_identity, remote_feed_receiver):
    identity = generate_rsa_identity(fast=True)
    request = Mock(remote_peer=identity.peer)
    model = htypes.remote_feed_receiver_tests.sample_list_feed()
    item = htypes.remote_feed_receiver_tests.sample_item(
        attr="Sample item",
        )
    diff = IndexListDiff.Append(item)
    remote_feed_receiver(request, model, diff.piece)
