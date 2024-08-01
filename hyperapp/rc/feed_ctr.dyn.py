from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.rc_constructor import Constructor


class FeedCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            element_t=pyobj_creg.invite(piece.element_t),
            )

    def __init__(self, t, element_t):
        self._t = t
        self._element_t = element_t

    @property
    def piece(self):
        return self._constructor_t(
            t=pyobj_creg.actor_to_ref(self._t),
            element_t=pyobj_creg.actor_to_ref(self._element_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        ready_tgt = target_set.factory.config_item_ready('feed_factory', self._type_name)
        ready_tgt.set_provider(resource_tgt, target_set)
        resolved_tgt = target_set.factory.config_item_resolved('feed_factory', self._type_name)
        resolved_tgt.resolve(self)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        target_set.update_deps_for(ready_tgt)
        target_set.update_deps_for(resolved_tgt)
        target_set.update_deps_for(resource_tgt)

    def make_component(self, python_module, name_to_res=None):
        feed = self._make_feed()
        if name_to_res is not None:
            name_to_res[self._component_name] = feed
        return feed

    def get_component(self, name_to_res):
        return name_to_res[self._component_name]

    @property
    def _type_name(self):
        return f'{self._t.module_name}_{self._t.name}'


class ListFeedCtr(FeedCtr):

    constructor_t = htypes.rc_constructors.list_feed

    def _make_feed(self):
        return htypes.ui.list_feed(
            element_t=pyobj_creg.actor_to_ref(self._element_t),
            )

    @property
    def _component_name(self):
        return f'{self._type_name}.list_feed'


class IndexTreeFeedCtr(FeedCtr):

    constructor_t = htypes.rc_constructors.index_tree_feed

    def _make_feed(self):
        return htypes.ui.index_tree_feed(
            element_t=pyobj_creg.actor_to_ref(self._element_t),
            )

    @property
    def _component_name(self):
        return f'{self._type_name}.index_tree_feed'
