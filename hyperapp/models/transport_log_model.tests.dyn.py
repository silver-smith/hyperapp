from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import transport_log_model


def test_model(bundler, generate_rsa_identity, transport_log):
    receiver = generate_rsa_identity(fast=True)
    sender = generate_rsa_identity(fast=True)
    msg = 'Sample message'
    msg_bundle = bundler([mosaic.put(msg)]).bundle
    parcel = receiver.peer.make_parcel(msg_bundle, sender)
    transport_bundle = bundler([mosaic.put(parcel.piece)]).bundle
    transport_log.add_out_message(parcel, msg_bundle)
    transport_log.commit_out_message(parcel, 'tcp', transport_bundle, 12345)

    piece = htypes.transport_log_model.model()
    item_list = transport_log_model.transport_log_model(piece)
    assert item_list


def test_open():
    model = transport_log_model.open_transport_log()
    assert model
