from .services import (
    code_registry_ctr,
    )


def identity_creg(config):
    return code_registry_ctr('identity_creg', config)


def peer_creg(config):
    return code_registry_ctr('peer_creg', config)


def signature_creg(config):
    return code_registry_ctr('signature_creg', config)


def parcel_creg(config):
    return code_registry_ctr('parcel_creg', config)


def route_creg(config):
    return code_registry_ctr('route_creg', config)
