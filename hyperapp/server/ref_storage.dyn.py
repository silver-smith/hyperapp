# storage for permanent references, backed by database table

import logging

from pony.orm import db_session, Required, PrimaryKey

from hyperapp.common.htypes import capsule_t
from hyperapp.common.ref import ref2str, str2ref, ref_repr
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


class RefStorage(object):

    def __init__(self, ref_resolver):
        self._ref_resolver = ref_resolver
        self._recursion_flag = False

    @db_session
    def resolve_ref(self, ref):
        if self._recursion_flag:
            return None  # Called from our store_ref
        rec = this_module.Ref.get(ref_hash_algorithm=ref.hash_algorithm, ref_hash=ref.hash)
        if not rec:
            return None
        return capsule_t(
            type_ref=str2ref(rec.type_ref),
            encoding=rec.encoding,
            encoded_object=rec.encoded_object,
            )

    @db_session
    def store_ref(self, ref):
        self._recursion_flag = True
        try:
            capsule = self._ref_resolver.resolve_ref(ref)
        finally:
            self._recursion_flag = False
        assert capsule, 'Can not store unknown ref: %s' % ref_repr(ref)
        rec = this_module.Ref.get(ref_hash_algorithm=ref.hash_algorithm, ref_hash=ref.hash)
        if rec:
            rec.type_ref = ref2str(capsule.type_ref)
            rec.encoding = capsule.encoding
            rec.encoded_object = capsule.encoded_object
        else:
            rec = this_module.Ref(
                ref_hash_algorithm=ref.hash_algorithm,
                ref_hash=ref.hash,
                type_ref=ref2str(capsule.type_ref),
                encoding=capsule.encoding,
                encoded_object=capsule.encoded_object,
                )
        log.info('Ref storage: ref %s is stored, type: %s, encoding: %s',
                 ref_repr(ref), ref_repr(capsule.type_ref), capsule.encoding)


class ThisModule(PonyOrmModule):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.ref_storage = self._ref_storage = RefStorage(services.ref_resolver)

    def init_phase_2(self, services):
        self.Ref = self.make_entity(
            'Ref',
            ref_hash_algorithm=Required(str),
            ref_hash=Required(bytes),
            type_ref=Required(str),
            encoding=Required(str),
            encoded_object=Required(bytes),
            primary_key=('ref_hash_algorithm', 'ref_hash'),
            )
        services.ref_resolver.add_source(self._ref_storage)
