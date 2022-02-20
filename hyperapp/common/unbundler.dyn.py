# register capsules and routes from a bundle


import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Unbundler(object):

    def __init__(self, mosaic, aux_unbundler_hooks):
        self._mosaic = mosaic
        self._aux_unbundler_hooks = aux_unbundler_hooks

    def register_bundle(self, bundle):
        for capsule in bundle.capsule_list:
            self._mosaic.register_capsule(capsule)
        for aux_ref in bundle.aux_roots:
            decoded_capsule = self._mosaic.resolve_ref(aux_ref)
            for hook in self._aux_unbundler_hooks:
                hook(aux_ref, decoded_capsule.t, decoded_capsule.value)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._aux_unbundler_hooks = []
        services.aux_unbundler_hooks = self._aux_unbundler_hooks
        services.unbundler = Unbundler(services.mosaic, self._aux_unbundler_hooks)
