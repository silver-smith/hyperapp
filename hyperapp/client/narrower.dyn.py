import logging
import asyncio
from PySide import QtCore, QtGui

from ..common.interface import core as core_types
from ..common.interface import narrower as narrower_types
from .util import uni2str, key_match, key_match_any
from .module import Module
from .object import ObjectObserver, Object
from .list_object import ListObserver, Chunk, ListObject
from .command import command
from . import view
from .line_list_panel import LineListPanel
from . import line_edit

log = logging.getLogger(__name__)


FETCH_ELEMENT_COUNT = 200  # how many rows to request when request is originating from narrower itself


# todo: subscription
class FilteredListObj(ListObject, ListObserver):

    def __init__(self, base, narrow_field_id, prefix):
        assert isinstance(base, ListObject), repr(base)
        log.debug('new FilteredListObj self=%s narrow_field_id=%r prefix=%r', id(self), narrow_field_id, prefix)
        ListObject.__init__(self)
        self._base = base
        self._narrow_field_id = narrow_field_id  # filter by this field
        self._prefix = prefix
        self._cached_elements = []
        self._base.subscribe(self)

    def __repr__(self):
        return 'FilteredListObj(%r/%r/%r)' % (self._narrow_field_id, self._prefix, len(self._cached_elements))

    def get_title(self):
        return self._base.get_title()

    def get_url(self):
        return self._base.get_url()

    def get_commands(self):
        return self._base.get_commands()

    def get_columns(self):
        return self._base.get_columns()

    def get_key_column_id(self):
        return self._base.get_key_column_id()
    
    async def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        log.info('-- narrower.fetch_elements sort_column_id=%r key=%r desc_count=%r asc_count=%r', sort_column_id, key, desc_count, asc_count)
        await self._base.fetch_elements(sort_column_id, key, desc_count, asc_count)

    def process_fetch_result(self, result):
        log.info('-- narrower.process_fetch_result sort_column_id=%r bof=%r eof=%r elements-len=%r', result.sort_column_id, result.bof, result.eof, len(result.elements))
        elements = list(filter(self._element_matched, result.elements))
        filtered = result.clone_with_elements(elements)
        # When there is no filtered elements list view can not fetch more elements - it does not have element key
        # to start from. So we issue fetch request ourselves. Yet we have to notify list view about eof.
        if not filtered.elements and result.elements and not result.eof:
            log.info('   > all filtered out, fetching more')
            asyncio.async(self._base.fetch_elements(
                result.sort_column_id, result.elements[-1].key, 1, FETCH_ELEMENT_COUNT))
        else:
            log.info('   > notify with %r elements', len(filtered.elements))
            self._notify_fetch_result(filtered)
        self._cached_elements.extend(elements)  # may has duplicates now, it's ok

    def _element_matched(self, element):
        value = self._get_filter_field(element)
        return value.lower().startswith(self._prefix.lower())

    async def run_command(self, command_id, **kw):
        return (await self._base.run_command(command_id, **kw))

    # we find only in cached elements, that is elements we have seen; do not issue additional fetch command
    def find_common_prefix(self):
        elements = self._cached_elements
        if not elements:
            return None
        common = self._get_filter_field(elements[0])
        for element in elements[1:]:
            field = self._get_filter_field(element)
            while not field.startswith(common):
                common = common[:-1]
        return common

    def _get_filter_field(self, element):
        return getattr(element.row, self._narrow_field_id)

    def __del__(self):
        log.debug('~FilteredListObj self=%s narrow_field_id=%r prefix=%r', id(self), self._narrow_field_id, self._prefix)


class NarrowerObject(Object):


    class FilterObserver(ObjectObserver):

        def __init__(self, narrower_object):
            self._narrower_object = narrower_object

        def object_changed(self):
            self._narrower_object._filter_changed()


    impl_id = 'narrower'

    @classmethod
    async def from_state(cls, state, objimpl_registry):
        filter_line = await objimpl_registry.resolve(state.filter_line)
        list_object = await objimpl_registry.resolve(state.list_object)
        return cls(filter_line, list_object)

    def __init__(self, filter_line, list_object):
        super().__init__()
        self._filter_line = filter_line
        self._list_object = list_object
        self._filter_observer = self.FilterObserver(self)
        self._filter_line.subscribe(self._filter_observer)

    def get_title(self):
        return 'Narrowed: %s' % self._list_object.get_title()

    def get_state(self):
        return narrower_types.narrower_object(self.impl_id, self._filter_line.get_state(), self._list_object.get_state())

    def _filter_changed(self):
        log.debug('NarrowerObject._filter_changed; new filter: %r', self._filter_line.line)


class NarrowerView(LineListPanel):

    impl_id = 'narrower'

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry, view_registry):
        narrower_object = await objimpl_registry.resolve(state.object)
        filter_line = await view_registry.resolve(locale, state.filter_line)
        list_view = await view_registry.resolve(locale, state.list_view)
        return cls(parent, narrower_object, filter_line, list_view)

    def __init__(self, parent, object, filter_line, list_view):
        super().__init__(parent, filter_line, list_view)
        self._object = object
        self._filter_line = filter_line
        self._list_view = list_view
        #self.cancel_narrowing.set_enabled(self._filter_line.get_object().line != '')

    def get_state(self):
        return narrower_types.narrower_view(
            view_id=self.impl_id,
            object=self._object.get_state(),
            filter_line=self._filter_line.get_state(),
            list_view=self._list_view.get_state(),
            )

    def get_commands(self, kinds=None):
        return LineListPanel.get_commands(self, ['view', 'object'])

    def _set_prefix(self, prefix):
        self._line_edit.setText('')
        self._update_prefix('')

    def _make_filtered_obj(self, prefix):
        return FilteredListObj(self._base_obj, self._narrow_field_id, prefix)

    def _update_prefix(self, text):
        key = self._list_view.get_current_key()
        object = self._make_filtered_obj(text)
        self._list_view.set_object(object)
        self._list_view.set_current_key(key, select_first=True)
        self.cancel_narrowing.set_enabled(text != '')

    def _on_text_edited(self, text):
        self._update_prefix(text)

    def is_list_event(self, evt):
        if key_match_any(evt, [
            'Period',
            'Slash',
            'Ctrl+A',
            ]):
            return True
        if not self._line_edit.text() and key_match(evt, 'Ctrl+Backspace'):
            return True
        return LineListPanel.is_list_event(self, evt)

    @command('wider', kind='object', enabled=False)
    def cancel_narrowing(self):
        if self._line_edit.text():
            self._set_prefix('')

    def eventFilter(self, obj, evt):
        if self._line_edit.text() and key_match(evt, 'Space'):
            self._fill_common_prefix()
            return True
        return LineListPanel.eventFilter(self, obj, evt)

    def _fill_common_prefix(self):
        common_prefix = self._list_view.get_object().find_common_prefix()
        if not common_prefix:
            return
        self._line_edit.setText(common_prefix)

    def __del__(self):
        log.debug('~NarrowerView self=%s list_view=%s title=%r', id(self), id(self._list_view), self._object.get_title())


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(services)
        services.objimpl_registry.register(NarrowerObject.impl_id, NarrowerObject.from_state, services.objimpl_registry)
        services.view_registry.register(NarrowerView.impl_id, NarrowerView.from_state, services.objimpl_registry, services.view_registry)
