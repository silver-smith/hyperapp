import logging
from collections import defaultdict, namedtuple
from contextlib import contextmanager

from .htypes.meta_association import meta_association

log = logging.getLogger(__name__)


Association = namedtuple('Association', 'bases key_to_value')


class AssociationRegistry:

    def __init__(self, meta_registry):
        self._meta_registry = meta_registry
        self._piece_to_ass = {}  # Association piece -> animated Association namedtuple.
        self._base_to_pieces = defaultdict(set)
        self._key_to_value = {}

    @contextmanager
    def associations_registered(self, ass_list):
        added_new = self.register_association_list(ass_list)
        try:
            yield
        finally:
            self.remove_associations(added_new)

    def register_association_list(self, ass_list):
        added_new = []
        for ass in ass_list:
            if isinstance(ass, meta_association):
                log.info("Register meta association: %r", ass)
                if self._register_association(ass):
                    added_new.append(ass)
        for ass in ass_list:
            if not isinstance(ass, meta_association):
                if self._register_association(ass):
                    added_new.append(ass)
        if added_new:
            self._update()
        return added_new
    
    def register_association(self, piece):
        if self._register_association(piece):
            self._update()

    def remove_associations(self, piece_list):
        for piece in piece_list:
            try:
                del self._piece_to_ass[piece]
            except KeyError:
                pass
        if piece_list:
            self._update()

    def __getitem__(self, key):
        return self._key_to_value[key]

    def pieces_for_base(self, base):
        return self._base_to_pieces.get(base, [])

    def _register_association(self, piece):
        ass = self._meta_registry.animate(piece)
        log.info("Register association: %r; record: %r", piece, ass)
        if not ass:
            return False  # Old-style registration function, registered directly.
        if piece in self._piece_to_ass:
            return False  # Already registered.
        self._piece_to_ass[piece] = ass
        return True

    def _update(self):
        self._base_to_pieces.clear()
        self._key_to_value.clear()
        for piece, ass in self._piece_to_ass.items():
            for base in ass.bases:
                self._base_to_pieces[base].add(piece)
            for key, value in ass.key_to_value.items():
                self._key_to_value[key] = value
