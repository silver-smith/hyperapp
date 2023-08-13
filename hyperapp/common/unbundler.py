# register capsules and routes from a bundle

import logging

from hyperapp.common.association_registry import Association

log = logging.getLogger(__name__)


class Unbundler:

    def __init__(self, web, mosaic, association_reg, python_object_creg, aux_unbundler_hooks):
        self._web = web
        self._mosaic = mosaic
        self._association_reg = association_reg
        self._python_object_creg = python_object_creg
        self._aux_unbundler_hooks = aux_unbundler_hooks

    def register_bundle(self, bundle):
        ref_set = set()
        for capsule in bundle.capsule_list:
            ref_set.add(self._mosaic.register_capsule(capsule))
        # Meta associations should be registered before others. So, collect association list first.
        ass_list = []
        for aux_ref in bundle.aux_roots:
            decoded_capsule = self._mosaic.resolve_ref(aux_ref)
            log.debug("Unbundle aux: %s %s: %s", aux_ref, decoded_capsule.t, decoded_capsule.value)
            handled_by_hook = False
            for hook in self._aux_unbundler_hooks:
                if hook(aux_ref, decoded_capsule.t, decoded_capsule.value):
                    log.debug("Unbundle aux: handled by hook: %s", hook)
                    handled_by_hook = True
            if not handled_by_hook:
                ass_list.append(
                    Association.from_piece(decoded_capsule.value, self._web, self._python_object_creg))
        self._association_reg.register_association_list(ass_list)
        return ref_set | set(bundle.aux_roots)
