import logging
from PySide import QtCore, QtGui

from .command import command
from .object import Object
from .view import View
from .registry import Registry
from .module import Module
from ..common.interface import object_selector as object_selector_types

log = logging.getLogger(__name__)


class ObjectSelectorObject(Object):

    impl_id = 'object_selector'

    @classmethod
    def from_state(cls, state):
        callback = this_module.callback_registry.resolve(state.callback)
        return cls(callback)

    def __init__(self, callback):
        Object.__init__(self)
        self._callback = callback

    def get_state(self):
        return object_selector_types.object_selector_object(self.impl_id)


class ObjectSelectorView(View, QtGui.QWidget):

    impl_id = 'object_selector'

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry, view_registry):
        object = await objimpl_registry.resolve(state.object)
        target_view = await view_registry.resolve(locale, state.target)
        return cls(parent, object, target_view)

    def __init__(self, parent, object, target_view):
        QtGui.QWidget.__init__(self)
        View.__init__(self, parent)
        self.object = object
        self.target_view = target_view
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Select object'))
        layout.addWidget(target_view.get_widget())
        self.setLayout(layout)
        target_view.set_parent(self)

    def get_state(self):
        target_handle = self.target_view.get_state()
        object = self.object.get_state()
        return object_selector_types.object_selector_view(self.impl_id, object, target_handle)

    def get_current_child(self):
        return self.target_view

    def open(self, handle):
        object = self.object.get_state()
        selector_handle = object_selector_types.object_selector_view(self.impl_id, object, handle)
        View.open(self, selector_handle)

    def get_command_list(self, kinds=None):
        command_list = super().get_command_list(kinds)
        if not kinds or 'object' in kinds:
            return command_list + [self.object_command_choose]  # do not wrap in ViewCommand - we will open it ourselves
        else:
            return command_list

    @command('choose', kind='object')
    async def object_command_choose(self):
        ref_list = self.target_view.pick_current_refs()
        print('*** ref_list =', ref_list)


class CallbackRegistry(Registry):

    def register(self, tclass, factory, *args, **kw):
        assert object_selector_types.object_selector_callback.is_my_class(tclass)
        super().register(tclass.id, factory, *args, **kw)

    def resolve(self, callback):
        tclass = object_selector_types.object_selector_callback.get_object_class(callback)
        rec = self._resolve(tclass.id)
        log.info('producing object selector callback %r using %s(%s, %s)', tclass.id, rec.factory, rec.args, rec.kw)
        return rec.factory(callback, *rec.args, **rec.kw)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.objimpl_registry.register(ObjectSelectorObject.impl_id, ObjectSelectorObject.from_state)
        services.view_registry.register(ObjectSelectorView.impl_id, ObjectSelectorView.from_state, services.objimpl_registry, services.view_registry)
        self.callback_registry = CallbackRegistry()

    def register_callback(self, id, factory, *args, **kw):
        self.callback_registry.register(id, factory, *args, **kw)
