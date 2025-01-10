# register capsules and routes from a bundle

import logging

from hyperapp.boot.association_registry import Association

log = logging.getLogger(__name__)


class Unbundler:

    def __init__(self, web, mosaic, association_reg):
        self._web = web
        self._mosaic = mosaic
        self._association_reg = association_reg

    def register_bundle(self, bundle, register_associations=True):
        ref_set = set()
        for capsule in bundle.capsule_list:
            ref_set.add(self._mosaic.register_capsule(capsule))
        if not register_associations:
            return ref_set
        # Meta associations should be registered before others. So, collect association list first.
        ass_list = []
        for ass_ref in bundle.associations:
            decoded_capsule = self._mosaic.resolve_ref(ass_ref)
            log.debug("Unbundle association: %s %s: %s", ass_ref, decoded_capsule.t, decoded_capsule.value)
            ass_list.append(
                Association.from_piece(decoded_capsule.value, self._web))
        self._association_reg.register_association_list(ass_list)
        return ref_set | set(bundle.associations)
