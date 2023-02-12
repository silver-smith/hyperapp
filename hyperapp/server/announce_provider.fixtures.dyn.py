from .services import (
    generate_rsa_identity,
    mark,
    mosaic,
    )


_phony_type = 'phony_type'

_phony_impl_registry = {
    _phony_type: ('phony_ctr_fn', 'phony_spec'),
    }


@mark.service
def impl_registry():
    return _phony_impl_registry


@mark.param.aux_bundler_hook
def server_peer_ref():
    identity = generate_rsa_identity(fast=True)
    return mosaic.put(identity.peer.piece)


@mark.param.aux_bundler_hook
def ref():
    return mosaic.put('phony_ref')


@mark.param.aux_bundler_hook
def t():
    return _phony_type


@mark.param.aux_bundler_hook
def value():
    return mosaic.put('phony_value')
