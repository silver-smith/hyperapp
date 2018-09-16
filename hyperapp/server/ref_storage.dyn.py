# storage for permanent references, backed by database table

import logging

from pony.orm import db_session, Required, PrimaryKey

from ..common.interface import hyper_ref as href_types
from ..common.util import full_type_name_to_str
from ..common.ref import ref_repr
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_storage'


class RefStorage(object):

    def __init__(self, ref_resolver):
        self._ref_resolver = ref_resolver
        self._recursion_flag = False

    @db_session
    def resolve_ref(self, ref):
        if self._recursion_flag:
            return None  # Called from our store_ref
        rec = this_module.Ref.get(ref=ref)
        if not rec:
            return None
        return href_types.capsule(
            full_type_name=rec.full_type_name.split('.'),
            hash_algorithm=rec.hash_algorithm,
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
            rec.full_type_name = '.'.join(capsule.full_type_name)
            rec.encoding = capsule.encoding
            rec.encoded_object = capsule.encoded_object
        else:
            rec = this_module.Ref(
                ref_hash_algorithm=ref.hash_algorithm,
                ref_hash=ref.hash,
                full_type_name=full_type_name_to_str(capsule.full_type_name),
                encoding=capsule.encoding,
                encoded_object=capsule.encoded_object,
                )
        log.info('Ref storage: ref %s is stored, type: %s, encoding: %s',
                     ref_repr(ref), full_type_name_to_str(capsule.full_type_name), capsule.encoding)


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_storage = ref_storage = RefStorage(services.ref_resolver)
        services.ref_resolver.add_source(ref_storage)

    def init_phase2(self, services):
        self.Ref = self.make_entity(
            'Ref',
            ref_hash_algorithm=Required(str),
            ref_hash=Required(bytes),
            full_type_name=Required(str),
            encoding=Required(str),
            encoded_object=Required(bytes),
            primary_key=('ref_hash_algorithm', 'ref_hash'),
            )
