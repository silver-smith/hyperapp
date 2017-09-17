import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.htypes import tString, tInt, TOptional, Field
from ..common.interface import core as core_types
from .util import uni2str, key_match, key_match_any
from .list_object import ListObserver, Chunk, ListObject
from .command import command
from . import view
from .line_list_panel import LineListPanel
from . import line_edit
from . import list_view

log = logging.getLogger(__name__)


NARROWER_VIEW_ID = 'narrower_list'
FETCH_ELEMENT_COUNT = 200  # how many rows to request when request is originating from narrower itself


def register_views(registry, services):
    registry.register(NARROWER_VIEW_ID, View.from_state, services.objimpl_registry, services.resources_manager)


tNarrowerListHandleBase = core_types.handle.register(
    'narrower_list_base', base=core_types.list_handle_base, fields=[
        Field('narrow_field_id', tString),
        ])

tStringNarrowerListHandle = core_types.handle.register(
    'string_narrower_list', base=tNarrowerListHandleBase, fields=[
        Field('key', TOptional(tString)),
        ])

tIntNarrowerListHandle = core_types.handle.register(
    'int_narrower_list', base=tNarrowerListHandleBase, fields=[
        Field('key', TOptional(tInt)),
        ])


def narrower_list_handle_type(key_t):
    if key_t is tString:
        return tStringNarrowerListHandle
    if key_t is tInt:
        return tIntNarrowerListHandle
    assert False, 'Unsupported list key type: %r' % key_t


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
    
    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        log.info('-- narrower.fetch_elements sort_column_id=%r key=%r desc_count=%r asc_count=%r', sort_column_id, key, desc_count, asc_count)
        yield from self._base.fetch_elements(sort_column_id, key, desc_count, asc_count)

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

    @asyncio.coroutine
    def run_command(self, command_id, **kw):
        return (yield from self._base.run_command(command_id, **kw))

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


class View(LineListPanel):

    view_id = NARROWER_VIEW_ID

    @classmethod
    @asyncio.coroutine
    def from_state(cls, locale, state, parent, objimpl_registry, resources_manager):
        data_type = core_types.handle.resolve_obj(state)
        object = objimpl_registry.resolve(state.object)
        return cls(locale, parent, data_type, object, resources_manager, state.resource_id,
                   state.sort_column_id, state.key, state.narrow_field_id)

    def __init__( self, locale, parent, data_type, object, resources_manager, resource_id, sort_column_id, key,
                  narrow_field_id, first_visible_row=None, select_first=True, prefix=None ):
        log.debug('new narrower self=%s', id(self))
        self._data_type = data_type
        self._base_obj = object
        self._resource_id = resource_id
        self._narrow_field_id = narrow_field_id
        line_edit_view = line_edit.View(self, prefix)
        list_view_view = list_view.View(
            locale, self, resources_manager, resource_id, None, object, key, sort_column_id, first_visible_row, select_first)
        LineListPanel.__init__(self, parent, line_edit_view, list_view_view)
        self._line_edit.textEdited.connect(self._on_text_edited)
        self.cancel_narrowing.set_enabled(bool(prefix))

    def get_state(self):
        return self._data_type(
            view_id=self.view_id,
            object=self._base_obj.get_state(),
            resource_id=self._resource_id,
            sort_column_id=self._list_view.get_sort_column_id(),
            key=self._list_view.get_current_key(),
            narrow_field_id=self._narrow_field_id,
            # lvs.first_visible_row, lvs.select_first, self._line_edit.text()
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
        log.debug('~narrower self=%s list_view=%s title=%r', id(self), id(self._list_view), self._base_obj.get_title())
