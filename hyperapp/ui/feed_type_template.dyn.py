from . import htypes
from .services import pyobj_creg
from .code.mark import mark


class FeedTypeTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            feed_type_ref=piece.feed_type,
            )

    def __init__(self, t, feed_type_ref):
        self._t = t
        self._feed_type_ref = feed_type_ref

    @property
    def piece(self):
        return htypes.feed.feed_template(
            t=pyobj_creg.actor_to_ref(self._t),
            feed_type=self._feed_type_ref,
            )

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        # Should resolve it here manually.
        # If added as dependency to from_piece, it fails resolving
        # because cfg_item_creg is a system resource and resolved
        # before regular resources such as feed_creg.
        feed_creg = system.resolve_service('feed_creg')
        return feed_creg.invite(self._feed_type_ref)
