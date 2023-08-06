from .services import (
    mark,
    )
from .code.dyn_code_registry import DynCodeRegistry


@mark.service
def identity_registry():
    return DynCodeRegistry('identity')


@mark.service
def peer_registry():
    return DynCodeRegistry('peer')


@mark.service
def signature_registry():
    return DynCodeRegistry('signature')


@mark.service
def parcel_registry():
    return DynCodeRegistry('parcel')
