# storage for permanent references, backed by database table

import logging

from pony.orm import db_session, Required, PrimaryKey

from ..common.interface import hyper_ref as href_types
from ..common.ref import make_capsule, make_ref
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_storage'


class RefStorage(object):

    @db_session
    def resolve_ref(self, ref):
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
    def store_ref(self, ref, capsule):
        rec = this_module.Ref.get(ref=ref)
        if rec:
            rec.full_type_name = '.'.join(capsule.full_type_name)
            rec.hash_algorithm = capsule.hash_algorithm
            rec.encoding = capsule.encoding
            rec.encoded_object = capsule.encoded_object
        else:
            rec = this_module.Ref(
                ref=ref,
                full_type_name='.'.join(capsule.full_type_name),
                hash_algorithm=capsule.hash_algorithm,
                encoding=capsule.encoding,
                encoded_object=capsule.encoded_object,
                )

    def add_object(self, t, object):
        capsule = make_capsule(t, object)
        ref = make_ref(capsule)
        self.store_ref(ref, capsule)
        return ref


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_storage = ref_storage = RefStorage()
        services.ref_resolver.add_source(ref_storage)

    def init_phase2(self, services):
        self.Ref = self.make_entity(
            'Ref',
            ref=PrimaryKey(bytes),
            full_type_name=Required(str),
            hash_algorithm=Required(str),
            encoding=Required(str),
            encoded_object=Required(bytes),
            )
