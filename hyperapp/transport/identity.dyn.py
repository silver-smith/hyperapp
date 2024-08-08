from .services import (
    code_registry_ctr2,
    )


def identity_registry(config):
    return code_registry_ctr2('identity', config)


def peer_registry(config):
    return code_registry_ctr2('peer', config)


def signature_registry(config):
    return code_registry_ctr2('signature', config)


def parcel_registry(config):
    return code_registry_ctr2('parcel', config)
