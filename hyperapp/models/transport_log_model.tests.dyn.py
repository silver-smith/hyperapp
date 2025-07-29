from datetime import datetime

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .tested.code import transport_log_model


@mark.fixture
def receiver(generate_rsa_identity):
    return generate_rsa_identity(fast=True)


@mark.fixture
def sender(generate_rsa_identity):
    return generate_rsa_identity(fast=True)


@mark.fixture.obj
def current_item(bundler, receiver, sender):
    msg = 'Sample message'
    msg_bundle = bundler([mosaic.put(msg)]).bundle
    parcel = receiver.peer.make_parcel(msg_bundle, sender)
    transport_bundle = bundler([mosaic.put(parcel.piece)]).bundle
    return htypes.transport_log_model.item(
        id=123,
        dt=datetime.now(),
        direction='in',
        transport_name='tcp',
        msg_title=msg,
        msg_bundle=msg_bundle,
        transport_bundle=transport_bundle,
        transport_size=1345,
        )


@mark.fixture.obj
def fill_log(bundler, transport_log, receiver, sender):
    msg = 'Sample message'
    msg_bundle = bundler([mosaic.put(msg)]).bundle
    parcel = receiver.peer.make_parcel(msg_bundle, sender)
    transport_bundle = bundler([mosaic.put(parcel.piece)]).bundle
    transport_log.add_out_message(parcel, msg_bundle)
    transport_log.commit_out_message(parcel, 'tcp', transport_bundle, 12345)


@mark.fixture
def piece():
    return htypes.transport_log_model.model()

def test_model(fill_log, piece):
    item_list = transport_log_model.transport_log_model(piece)
    assert item_list


def test_message(fill_log, piece, current_item):
    model = transport_log_model.message(piece, current_item)
    assert model


def test_message_bundle(fill_log, piece, current_item):
    model = transport_log_model.message_bundle(piece, current_item)
    assert model


def test_transport_bundle(fill_log, piece, current_item):
    model = transport_log_model.transport_bundle(piece, current_item)
    assert model


def test_open():
    model = transport_log_model.open_transport_log()
    assert model
