from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr
from .code.cfg_item_req import CfgItemReq


class FeedCtr(ModuleCtr):

    def __init__(self, module_name, model_t):
        super().__init__(module_name)
        self._model_t = model_t

    def update_resource_targets(self, resource_tgt, target_set):
        req = CfgItemReq.from_actor('feed_factory', self._model_t)
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            'feed_factory', self._type_name, req, provider=resource_tgt, ctr=self)
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def make_component(self, types, python_module, name_to_res=None):
        feed_type = self._make_feed_type()
        template = htypes.feed.feed_template(
            feed_type=mosaic.put(feed_type),
            )
        cfg_item = htypes.cfg_item.typed_cfg_item(
            t=pyobj_creg.actor_to_ref(self._model_t),
            value=mosaic.put(template),
            )
        if name_to_res is not None:
            name_to_res[f'{self._type_name}.feed-type'] = feed_type
            name_to_res[f'{self._type_name}.feed-template'] = template
            name_to_res[self._component_name] = cfg_item
        return template

    def get_component(self, name_to_res):
        return name_to_res[self._component_name]

    @property
    def _component_name(self):
        return f'{self._type_name}.feed-template-cfg-item'

    @property
    def _type_name(self):
        return f'{self._model_t.module_name}-{self._model_t.name}'


class MultiItemFeedCtr(FeedCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            model_t=pyobj_creg.invite(piece.model_t),
            item_t=pyobj_creg.invite(piece.item_t) if piece.item_t is not None else None,
            )

    def __init__(self, module_name, model_t, item_t):
        super().__init__(module_name, model_t)
        self._item_t = item_t

    def __eq__(self, rhs):
        if type(self) is not type(rhs):
            return False
        if self._module_name != rhs._module_name:
            return False
        if self._model_t is not rhs._model_t:
            return False
        if self._item_t is not rhs._item_t:
            return False
        return True

    @property
    def piece(self):
        return self._constructor_t(
            module_name=self._module_name,
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            item_t=pyobj_creg.actor_to_ref(self._item_t) if self._item_t is not None else None,
            )


class ListFeedCtr(MultiItemFeedCtr):

    _constructor_t = htypes.feed.list_feed_ctr

    def _make_feed_type(self):
        return htypes.feed.list_feed_type(
            item_t=pyobj_creg.actor_to_ref(self._item_t) if self._item_t is not None else None,
            )


class IndexTreeFeedCtr(MultiItemFeedCtr):

    _constructor_t = htypes.feed.index_tree_feed_ctr

    def _make_feed_type(self):
        return htypes.feed.index_tree_feed_type(
            item_t=pyobj_creg.actor_to_ref(self._item_t) if self._item_t is not None else None,
            )


class ValueFeedCtr(FeedCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            model_t=pyobj_creg.invite(piece.model_t),
            value_t=pyobj_creg.invite(piece.value_t),
            )

    def __init__(self, module_name, model_t, value_t):
        super().__init__(module_name, model_t)
        self._value_t = value_t

    def __eq__(self, rhs):
        if type(self) is not type(rhs):
            return False
        if self._module_name != rhs._module_name:
            return False
        if self._model_t is not rhs._model_t:
            return False
        if self._value_t is not rhs._value_t:
            return False
        return True

    @property
    def piece(self):
        return htypes.feed.value_feed_ctr(
            module_name=self._module_name,
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            )

    def _make_feed_type(self):
        return htypes.feed.value_feed_type(
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            )
