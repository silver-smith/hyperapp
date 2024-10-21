from .services import (
    code_registry_ctr2,
    )


def identity_registry(config):
    return code_registry_ctr2('identity_registry', config)


def peer_registry(config):
    return code_registry_ctr2('peer_registry', config)


def signature_registry(config):
    return code_registry_ctr2('signature_registry', config)


def parcel_registry(config):
    return code_registry_ctr2('parcel_registry', config)
