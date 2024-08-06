from .services import (
    code_registry_ctr,
    )


def identity_registry():
    return code_registry_ctr('identity')


def peer_registry():
    return code_registry_ctr('peer')


def signature_registry():
    return code_registry_ctr('signature')


def parcel_registry():
    return code_registry_ctr('parcel')
