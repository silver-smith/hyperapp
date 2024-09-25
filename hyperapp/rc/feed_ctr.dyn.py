from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr


class FeedCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            t=pyobj_creg.invite(piece.t),
            element_t=pyobj_creg.invite(piece.element_t),
            )

    def __init__(self, module_name, t, element_t):
        super().__init__(module_name)
        self._t = t
        self._element_t = element_t

    def __eq__(self, rhs):
        if type(self) is not type(rhs):
            return False
        if self._module_name != rhs._module_name:
            return False
        if self._t is not rhs._t:
            return False
        if self._element_t is not rhs._element_t:
            return False
        return True

    @property
    def piece(self):
        return self._constructor_t(
            module_name=self._module_name,
            t=pyobj_creg.actor_to_ref(self._t),
            element_t=pyobj_creg.actor_to_ref(self._element_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        ready_tgt = target_set.factory.config_item_ready('feed_factory', self._type_name)
        ready_tgt.set_provider(resource_tgt, target_set)
        resolved_tgt = target_set.factory.config_item_resolved('feed_factory', self._type_name)
        resolved_tgt.resolve(self)
        # Should be created to be added to config resource.
        _ = target_set.factory.config_item_complete('feed_factory', self._type_name)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        target_set.update_deps_for(ready_tgt)
        target_set.update_deps_for(resolved_tgt)
        target_set.update_deps_for(resource_tgt)

    def make_component(self, types, python_module, name_to_res=None):
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

    _constructor_t = htypes.rc_constructors.list_feed

    def _make_feed(self):
        return htypes.ui.list_feed(
            element_t=pyobj_creg.actor_to_ref(self._element_t),
            )

    @property
    def _component_name(self):
        return f'{self._type_name}.list_feed'


class IndexTreeFeedCtr(FeedCtr):

    _constructor_t = htypes.rc_constructors.index_tree_feed

    def _make_feed(self):
        return htypes.ui.index_tree_feed(
            element_t=pyobj_creg.actor_to_ref(self._element_t),
            )

    @property
    def _component_name(self):
        return f'{self._type_name}.index_tree_feed'
