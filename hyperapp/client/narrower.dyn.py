import logging
import asyncio
from PySide import QtCore, QtGui

from hyperapp.client.util import uni2str, key_match, key_match_any
from hyperapp.client.object import ObjectObserver, Object
from hyperapp.client.list_object import ListObserver, Chunk, ListObject
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from .line_list_panel import LineListPanel
from . import line_edit
from . import htypes

log = logging.getLogger(__name__)


MODULE_NAME = 'narrower'


class NarrowerObject(Object):


    class FilterObserver(ObjectObserver):

        def __init__(self, narrower_object):
            self._narrower_object = narrower_object

        def object_changed(self):
            self._narrower_object._filter_changed()


    impl_id = 'narrower'

    @classmethod
    async def from_state(cls, filter_line, list_object, state):
        return cls(filter_line, list_object, state.filtered_field)

    def __init__(self, filter_line, list_object, filtered_field):
        super().__init__()
        self._filter_line = filter_line
        self._list_object = list_object
        self._filtered_field = filtered_field
        self._filter_observer = self.FilterObserver(self)
        self._filter_line.subscribe(self._filter_observer)
        self._list_object.set_filter(self._list_filter)
        self.cancel_narrowing.set_enabled(self._filter_line.line != '')

    def get_title(self):
        return 'Narrowed: %s' % self._list_object.get_title()

    def get_state(self):
        return htypes.narrower.narrower_object(self.impl_id, self._filtered_field)

    @command('wider', enabled=False)
    def cancel_narrowing(self):
        if self._filter_line.line:
            self._filter_line.line = ''

    def _filter_changed(self):
        log.debug('NarrowerObject._filter_changed; new filter: %r', self._filter_line.line)
        self._list_object._notify_object_changed()
        self.cancel_narrowing.set_enabled(self._filter_line.line != '')

    def _list_filter(self, row):
        # log.debug('NarrowerObject._list_filter, filtered_field=%r, row=%r, line=%r, result=%r',
        #               self._filtered_field, row, self._filter_line.line, self._filter_line.line in getattr(row, self._filtered_field))
        if not self._filter_line.line:
            return True
        return self._filter_line.line in getattr(row, self._filtered_field)


class NarrowerView(LineListPanel):

    impl_id = 'narrower'

    @classmethod
    async def from_state(cls, locale, state, parent, view_registry):
        filter_line = await view_registry.resolve_async(locale, state.filter_line)
        list_view = await view_registry.resolve_async(locale, state.list_view)
        narrower_object = await NarrowerObject.from_state(filter_line.get_object(), list_view.get_object(), state.object)
        return cls(parent, narrower_object, filter_line, list_view)

    def __init__(self, parent, object, filter_line, list_view):
        super().__init__(parent, filter_line, list_view)
        self._object = object
        self._filter_line = filter_line
        self._list_view = list_view
        self._filter_line.set_parent(self)
        self._list_view.set_parent(self)
        self._object.subscribe(self)

    def get_state(self):
        return htypes.narrower.narrower_view(
            view_id=self.impl_id,
            object=self._object.get_state(),
            filter_line=self._filter_line.get_state(),
            list_view=self._list_view.get_state(),
            )

    def get_object(self):
        return self._object

    def is_list_event(self, evt):
        if key_match_any(evt, [
            'Ctrl+A',
            ]):
            return True
        return LineListPanel.is_list_event(self, evt)

##    def is_list_event(self, evt):
##        if key_match_any(evt, [
##            'Period',
##            'Slash',
##            'Ctrl+A',
##            ]):
##            return True
##        if not self._line_edit.text() and key_match(evt, 'Ctrl+Backspace'):
##            return True
##        return LineListPanel.is_list_event(self, evt)
##
##    def eventFilter(self, obj, evt):
##        if self._line_edit.text() and key_match(evt, 'Space'):
##            self._fill_common_prefix()
##            return True
##        return LineListPanel.eventFilter(self, obj, evt)
##
##    def _fill_common_prefix(self):
##        common_prefix = self._list_view.get_object().find_common_prefix()
##        if not common_prefix:
##            return
##        self._line_edit.setText(common_prefix)

    def __del__(self):
        log.debug('~NarrowerView self=%s list_view=%s title=%r', id(self), id(self._list_view), self._object.get_title())


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        # hack to just make application storage and dynamic module registry's get_dynamic_module_id happy, not used otherwise:
        services.objimpl_registry.register(NarrowerObject.impl_id, NarrowerObject.from_state)
        services.view_registry.register(NarrowerView.impl_id, NarrowerView.from_state, services.view_registry)
