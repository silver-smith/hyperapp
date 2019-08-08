from hyperapp.common.htypes import resource_key_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.client.module import ClientModule
from .list_object import ListObject
from .list_view import ListView
from .tree_object import TreeObject
from .tree_view import TreeView
from .text_object import TextObject
from .text_view import TextView

MODULE_NAME = 'view_producer'


class ViewProducer:

    def __init__(self, type_resolver, resource_resolver):
        self._type_resolver = type_resolver
        self._resource_resolver = resource_resolver
        self._locale = 'en'

    def produce_view(self, state, object, observer):
        if isinstance(object, ListObject):
            return self._make_list_view(state, object, observer)
        if isinstance(object, TreeObject):
            return self._make_tree_view(state, object, observer)
        if isinstance(object, TextObject):
            return self._make_text_view(state, object, observer)
        assert False, repr(object)

    def _make_list_view(self, state, object, observer):
        columns = list(self._map_columns_to_view(state, object.get_columns()))
        list_view = ListView(columns, object)
        list_view.add_observer(observer)
        return list_view

    def _make_tree_view(self, state, object, observer):
        columns = list(self._map_columns_to_view(state, object.get_columns()))
        tree_view = TreeView(columns, object)
        tree_view.add_observer(observer)
        return tree_view

    def _make_text_view(self, state, object, observer):
        return TextView(object)

    def _state_type_ref(self, state):
        current_t = deduce_value_type(state)
        return self._type_resolver.reverse_resolve(current_t)

    def _map_columns_to_view(self, state, column_list):
        type_ref = self._state_type_ref(state)
        for column in column_list:
            resource_key = resource_key_t(type_ref, ['column', column.id])
            resource = self._resource_resolver.resolve(resource_key, self._locale)
            if resource:
                if not resource.is_visible:
                    continue
                text = resource.text
            else:
                text = column.id
            yield column.to_view_column(text)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.view_producer = ViewProducer(
            services.type_resolver,
            services.resource_resolver,
            )
