# register capsules and routes from a bundle

import logging

log = logging.getLogger(__name__)


class Unbundler:

    def __init__(self, mosaic, association_reg, aux_unbundler_hooks):
        self._mosaic = mosaic
        self._association_reg = association_reg
        self._aux_unbundler_hooks = aux_unbundler_hooks

    def register_bundle(self, bundle):
        for capsule in bundle.capsule_list:
            self._mosaic.register_capsule(capsule)
        for aux_ref in bundle.aux_roots:
            decoded_capsule = self._mosaic.resolve_ref(aux_ref)
            log.debug("Unbundle aux: %s %s: %s", aux_ref, decoded_capsule.t, decoded_capsule.value)
            handled_by_hook = False
            for hook in self._aux_unbundler_hooks:
                if hook(aux_ref, decoded_capsule.t, decoded_capsule.value):
                    log.debug("Unbundle aux: handled by hook: %s", hook)
                    handled_by_hook = True
            if not handled_by_hook:
                self._association_reg.register_association(decoded_capsule.value)
