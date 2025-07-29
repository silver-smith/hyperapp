from unittest.mock import Mock

from .services import (
    mosaic,
    )
from .code.mark import mark
from .tested.code import transport_log as tested_module


def test_log(bundler, generate_rsa_identity, transport_log):
    receiver = generate_rsa_identity(fast=True)
    sender = generate_rsa_identity(fast=True)
    msg = 'Sample message'
    msg_bundle = bundler([mosaic.put(msg)]).bundle
    parcel = receiver.peer.make_parcel(msg_bundle, sender)
    transport_bundle = bundler([mosaic.put(parcel.piece)]).bundle

    hook = Mock()
    transport_log.add_hook(hook)

    transport_log.add_out_message(parcel, msg_bundle)
    transport_log.commit_out_message(parcel, 'tcp', transport_bundle, 12345)

    hook.assert_called_once()

    transport_log.add_in_message(parcel, 'tcp', transport_bundle, 12345)
    transport_log.commit_in_message(parcel, msg_bundle)
