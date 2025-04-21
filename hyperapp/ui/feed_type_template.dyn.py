from . import htypes
from .services import pyobj_creg
from .code.mark import mark


class FeedTypeTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            model_t=pyobj_creg.invite(piece.model_t),
            feed_type_ref=piece.feed_type,
            )

    def __init__(self, model_t, feed_type_ref):
        self._model_t = model_t
        self._feed_type_ref = feed_type_ref

    @property
    def piece(self):
        return htypes.feed.feed_template(
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            feed_type=self._feed_type_ref,
            )

    @property
    def key(self):
        return self._model_t

    def resolve(self, system, service_name):
        # Should resolve it here manually.
        # If added as dependency to from_piece, it fails resolving
        # because cfg_item_creg is a system resource and resolved
        # before regular resources such as feed_type_creg.
        feed_type_creg = system.resolve_service('feed_type_creg')
        return feed_type_creg.invite(self._feed_type_ref)
