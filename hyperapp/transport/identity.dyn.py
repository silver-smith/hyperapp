from .services import (
    mark,
    types,
    web,
    )
from .code.dyn_code_registry import DynCodeRegistry


@mark.service
def identity_registry():
    return DynCodeRegistry('identity', web, types)


@mark.service
def peer_registry():
    return DynCodeRegistry('peer', web, types)


@mark.service
def signature_registry():
    return DynCodeRegistry('signature', web, types)


@mark.service
def parcel_registry():
    return DynCodeRegistry('parcel', web, types)
