from . import htypes
from .services import pyobj_creg
from .code.mark import mark


class FeedTypeTemplate:

    @classmethod
    @mark.actor.cfg_item_creg(htypes.feed.feed_template)
    def from_piece(cls, piece, feed_creg):
        return cls(
            feed_creg=feed_creg,
            t=pyobj_creg.invite(piece.t),
            feed_type=feed_creg.invite(piece.feed_type),
            )

    def __init__(self, feed_creg, t, feed_type):
        self._feed_creg = feed_creg
        self._t = t
        self._feed_type = feed_type

    @property
    def piece(self):
        return htypes.feed.feed_template(
            t=pyobj_creg.actor_to_ref(self._t),
            feed_type=self._feed_creg.actor_to_ref(self._feed_type),
            )

    @property
    def key(self):
        return self.t

    def resolve(self, system, service_name):
        return self._feed_type
