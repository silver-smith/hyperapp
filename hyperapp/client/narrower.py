from PySide import QtCore, QtGui
from ..common.interface import tString, Field, TRecord, tObject, tBaseObject, tHandle
from .util import uni2str, key_match, key_match_any
from .list_object import ListObserver, Slice, ListObject
from .objimpl_registry import objimpl_registry
from .view_command import command
from .view_registry import view_registry
from . import view
from .line_list_panel import LineListPanel
from . import line_edit
from . import list_view


FETCH_ELEMENT_COUNT = 200  # how many rows to request when request is originating from narrower itself


class Handle(list_view.Handle):

    @classmethod
    def from_data( cls, contents, server=None ):
        data_type = tHandle.resolve_obj(contents)
        object = objimpl_registry.produce_obj(contents.object, server)
        return cls(data_type, object, contents.sort_column_id, contents.key,
                   first_visible_row=None, select_first=True, narrow_field_id=contents.narrow_field_id)

    def __init__( self, data_type, object, sort_column_id, key,
                  first_visible_row, select_first, narrow_field_id, prefix=None ):
        assert prefix is None or isinstance(prefix, basestring), repr(prefix)
        list_view.Handle.__init__(self, data_type, object, sort_column_id, key, first_visible_row, select_first)
        self.narrow_field_id = narrow_field_id
        self.prefix = prefix

    def to_data( self ):
        return self.data_type.instantiate(
            'list_narrower',
            self.object.to_data(),
            self.sort_column_id,
            self.key,
            self.narrow_field_id,
            )

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        print 'narrower construct', parent, self.object.get_title(), self.sort_column_id, self.narrow_field_id, repr(self.prefix)
        return View(parent, self.data_type, self.object, self.sort_column_id, self.key,
                    self.first_visible_row, self.select_first, self.narrow_field_id, self.prefix)

    def __repr__( self ):
        return 'narrower.Handle(%r/%r/%r)' \
          % (uni2str(self.get_title()), self.narrow_field_id, self.prefix)


# todo: subscription
class FilteredListObj(ListObject, ListObserver):

    data_type = tObject.register('filtered_list', base=tBaseObject, fields=[
        Field('base', tObject),
        Field('narrow_field_id', tString),
        Field('prefix', tString),
        ])

    @classmethod
    def from_data( cls, rec, server=None ):
        base = objimpl_registry.produce_obj(rec.base, server)
        return cls(base, rec.narrow_field_id, rec.prefix)

    def __init__( self, base, narrow_field_id, prefix ):
        assert isinstance(base, ListObject), repr(base)
        ListObject.__init__(self)
        self._base = base
        self._narrow_field_id = narrow_field_id  # filter by this field
        self._prefix = prefix
        self._cached_elements = []
        self._base.subscribe(self)

    def __repr__( self ):
        return 'FilteredListObj(%r/%r/%r)' % (self._narrow_field_id, self._prefix, len(self._cached_elements))

    def to_data( self ):
        return self.data_type.instantiate(
            'filtered_list',
            self._base.to_data(),
            self._narrow_field_id,
            self._prefix,
            )

    def get_title( self ):
        return 'filtered(%r, %s)' % (self._prefix, self._base.get_title())

    def get_url( self ):
        return self._base.get_url()

    def get_commands( self ):
        return self._base.get_commands()

    def get_columns( self ):
        return self._base.get_columns()

    def get_key_column_id( self ):
        return self._base.get_key_column_id()
    
    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        print '-- narrower.fetch_elements', sort_column_id, `key`, desc_count, asc_count
        self._base.fetch_elements(sort_column_id, key, desc_count, asc_count)

    def process_fetch_result( self, result ):
        print '-- narrower.process_fetch_result', result.sort_column_id, result.bof, result.eof, len(result.elements)
        elements = filter(self._element_matched, result.elements)
        filtered = result.clone_with_elements(elements)
        # When there is no filtered elements list view can not fetch more elements - it does not have element key
        # to start from. So we issue fetch request ourselves. Yet we have to notify list view about eof.
        if not filtered.elements and result.elements and not result.eof:
            print '   > all filtered out, fetching more'
            self._base.fetch_elements(
                result.sort_column_id, result.elements[-1].key, result.direction, FETCH_ELEMENT_COUNT)
        else:
            print '   > notify with', len(filtered.elements)
            self._notify_fetch_result(filtered)
        self._cached_elements.extend(elements)  # may has duplicates now, it's ok

    def _element_matched( self, element ):
        value = self._get_filter_field(element)
        return value.lower().startswith(self._prefix.lower())

    def run_command( self, command_id, initiator_view, **kw ):
        return self._base.run_command(command_id, initiator_view, **kw)

    # we find only in cached elements, that is elements we have seen; do not issue additional fetch command
    def find_common_prefix( self ):
        elements = self._cached_elements
        if not elements:
            return None
        common = self._get_filter_field(elements[0])
        for element in elements[1:]:
            field = self._get_filter_field(element)
            while not field.startswith(common):
                common = common[:-1]
        return common

    def _get_filter_field( self, element ):
        return getattr(element.row, self._narrow_field_id)

    def __del__( self ):
        print '~FilteredListObj', repr(self._narrow_field_id), repr(self._prefix)


class View(LineListPanel):

    def __init__( self, parent, data_type, object, sort_column_id, key,
                  first_visible_row, select_first, narrow_field_id, prefix ):
        self._base_obj = object
        self._narrow_field_id = narrow_field_id
        list_object = self._filtered_obj(prefix)
        line_edit_handle = line_edit.Handle(prefix)
        list_handle = list_view.Handle(data_type, object, sort_column_id, key, first_visible_row, select_first)
        LineListPanel.__init__(self, parent, line_edit_handle, list_handle)
        self._line_edit.textEdited.connect(self._on_text_edited)
        self.cancel_narrowing.setEnabled(bool(prefix))

    def handle( self ):
        lh = self._list_view.handle()
        return Handle(lh.data_type, lh.object, lh.sort_column_id, lh.key, lh.first_visible_row, lh.select_first,
                      self._narrow_field_id, self._line_edit.text())

    def get_title( self ):
        return self._base_obj.get_title()

    def get_object( self ):
        return self._base_obj

    def _set_prefix( self, prefix ):
        self._line_edit.setText('')
        self._update_prefix('')

    def _filtered_obj( self, prefix ):
        return FilteredListObj(self._base_obj, self._narrow_field_id, prefix)

    def _update_prefix( self, text ):
        key = self._list_view.get_current_key()
        object = self._filtered_obj(text)
        self._list_view.set_object(object)
        self._list_view.set_current_key(key, select_first=True)
        self.cancel_narrowing.setEnabled(text != '')

    def _on_text_edited( self, text ):
        self._update_prefix(text)

    def is_list_event( self, evt ):
        if key_match_any(evt, [
            'Period',
            'Slash',
            'Ctrl+A',
            ]):
            return True
        if not self._line_edit.text() and key_match(evt, 'Ctrl+Backspace'):
            return True
        return LineListPanel.is_list_event(self, evt)

    @command('Wider', 'Cancel narrowing', ['Escape'], enabled=False)
    def cancel_narrowing( self ):
        if self._line_edit.text():
            self._set_prefix('')

    def eventFilter( self, obj, evt ):
        if self._line_edit.text() and key_match(evt, 'Space'):
            self._fill_common_prefix()
            return True
        return LineListPanel.eventFilter(self, obj, evt)

    def _fill_common_prefix( self ):
        common_prefix = self._list_view.get_object().find_common_prefix()
        if not common_prefix:
            return
        self._line_edit.setText(common_prefix)

    def __del__( self ):
        print '~narrower', self._base_obj.get_title(), self


objimpl_registry.register('filtered_list', FilteredListObj.from_data)
view_registry.register('list_narrower', Handle.from_data)
