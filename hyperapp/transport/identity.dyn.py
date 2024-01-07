from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def identity_registry():
    return code_registry_ctr('identity')


@mark.service
def peer_registry():
    return code_registry_ctr('peer')


@mark.service
def signature_registry():
    return code_registry_ctr('signature')


@mark.service
def parcel_registry():
    return code_registry_ctr('parcel')
