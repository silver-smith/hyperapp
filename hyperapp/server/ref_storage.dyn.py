# storage for permanent references, backed by database table

import logging

from pony.orm import db_session, Required, PrimaryKey

from ..common.interface import hyper_ref as href_types
from ..common.ref import make_piece, make_ref
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_storage'


class RefStorage(object):

    @db_session
    def resolve_ref(self, ref):
        rec = this_module.Ref.get(ref=ref)
        if not rec:
            return None
        return href_types.piece(
            full_type_name=rec.full_type_name.split('.'),
            hash_algorithm=rec.hash_algorithm,
            encoding=rec.encoding,
            encoded_object=rec.encoded_object,
            )

    @db_session
    def store_ref(self, ref, piece):
        rec = this_module.Ref.get(ref=ref)
        if rec:
            rec.full_type_name = '.'.join(piece.full_type_name)
            rec.hash_algorithm = piece.hash_algorithm
            rec.encoding = piece.encoding
            rec.encoded_object = piece.encoded_object
        else:
            rec = this_module.Ref(
                ref=ref,
                full_type_name='.'.join(piece.full_type_name),
                hash_algorithm=piece.hash_algorithm,
                encoding=piece.encoding,
                encoded_object=piece.encoded_object,
                )

    def add_object(self, t, object):
        piece = make_piece(t, object)
        ref = make_ref(piece)
        self.store_ref(ref, piece)
        return ref


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_storage = ref_storage = RefStorage()
        services.ref_resolver.add_source(ref_storage)

    def init_phase2(self):
        self.Ref = self.make_entity(
            'Ref',
            ref=PrimaryKey(bytes),
            full_type_name=Required(str),
            hash_algorithm=Required(str),
            encoding=Required(str),
            encoded_object=Required(bytes),
            )
