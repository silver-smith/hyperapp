# register capsules and routes from a bundle


import logging

from hyperapp.common.ref import LOCAL_TRANSPORT_REF
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Unbundler(object):

    def __init__(self, types, mosaic, aux_ref_unbundler_hooks):
        self._types = types
        self._mosaic = mosaic
        self._aux_ref_unbundler_hooks = aux_ref_unbundler_hooks

    def register_bundle(self, bundle):
        for capsule in bundle.capsule_list:
            self._mosaic.register_capsule(capsule)
        for aux_ref in bundle.aux_roots:
            decoded_capsule = self._types.resolve_ref(aux_ref)
            for hook in self._aux_ref_unbundler_hooks:
                hook(aux_ref, decoded_capsule.t, decoded_capsule.value)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._aux_ref_unbundler_hooks = []
        services.aux_ref_unbundler_hooks = self._aux_ref_unbundler_hooks
        services.unbundler = Unbundler(services.types, services.mosaic, self._aux_ref_unbundler_hooks)
