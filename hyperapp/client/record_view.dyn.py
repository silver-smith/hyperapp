from PySide import QtCore, QtGui

from hyperapp.client.module import ClientModule
from . import htypes
from .record_object import RecordObject
from .layout_registry import LayoutViewProducer


class RecordView(QtGui.QWidget):

    @classmethod
    async def make(cls, object_registry, view_producer, layout_resolver, object, observer, layout=None):
        view = cls(object)
        await view._construct(object_registry, view_producer, layout_resolver, observer, layout)
        return view

    def __init__(self, object):
        super().__init__()
        self._object = object
        self._field_views = None

    def get_title(self):
        return self._object.get_title()

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self._field_views[0].setFocus()

    async def _construct(self, object_registry, view_producer, layout_resolver, observer, layout):
        if layout:
            field_to_layout_ref = {field.field_id: field.layout_ref for field in layout.fields}
        else:
            field_to_layout_ref = {}
        qt_layout = QtGui.QVBoxLayout()
        has_expandable_field = False
        self._field_views = []
        for field_id, field_rec in self._object.get_fields().items():
            layout_ref = field_to_layout_ref.get(field_id)
            if layout_ref:
                producer = await layout_resolver.resolve(layout_ref)
            else:
                producer = view_producer
            field_view = await self._construct_field_view(object_registry, producer, qt_layout, field_id, field_rec, observer, layout)
            if field_view.sizePolicy().verticalPolicy() & QtGui.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_views.append(field_view)
        if not has_expandable_field:
            qt_layout.addStretch()
        self.setLayout(qt_layout)

    async def _construct_field_view(self, object_registry, producer, qt_layout, field_id, field_rec, observer, layout):
        field_object = await object_registry.resolve_async(field_rec)
        field_view = await producer.produce_view(field_rec, field_object, observer)
        label = QtGui.QLabel(field_id)
        label.setBuddy(field_view)
        qt_layout.addWidget(label)
        qt_layout.addWidget(field_view)
        qt_layout.addSpacing(10)
        return field_view


class RecordViewProducer(LayoutViewProducer):

    def __init__(self, layout, object_registry, view_producer, layout_resolver):
        self._layout = layout
        self._object_registry = object_registry
        self._view_producer = view_producer
        self._layout_resolver = layout_resolver

    async def produce_view(self, piece, object, observer=None):
        return (await RecordView.make(self._object_registry, self._view_producer, self._layout_resolver, object, observer, self._layout))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._object_registry = services.object_registry
        self._view_producer = services.view_producer
        self._layout_resolver = services.layout_resolver
        services.view_producer_registry.register_view_producer(self._produce_view)
        services.layout_registry.register_type(
            htypes.record_view.record_view_layout, RecordViewProducer, services.object_registry, services.view_producer, services.layout_resolver)

    async def _produce_view(self, piece, object, observer):
        if not isinstance(object, RecordObject):
            raise NotApplicable(object)
        return (await RecordView.make(self._object_registry, self._view_producer, self._layout_resolver, object, observer))
