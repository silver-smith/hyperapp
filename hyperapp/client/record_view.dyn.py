from PySide import QtCore, QtGui

from hyperapp.client.module import ClientModule
from .record_object import RecordObject


class RecordView(QtGui.QWidget):

    @classmethod
    async def make(cls, object_registry, view_producer, object):
        view = cls(object)
        await view._construct(object_registry, view_producer)
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

    async def _construct(self, object_registry, view_producer):
        layout = QtGui.QVBoxLayout()
        has_expandable_field = False
        self._field_views = []
        for field_id, field_rec in self._object.get_fields().items():
            field_view = await self._construct_field_view(object_registry, view_producer, layout, field_id, field_rec)
            if field_view.sizePolicy().verticalPolicy() & QtGui.QSizePolicy.ExpandFlag:
                has_expandable_field = True
            self._field_views.append(field_view)
        if not has_expandable_field:
            layout.addStretch()
        self.setLayout(layout)

    async def _construct_field_view(self, object_registry, view_producer, layout, field_id, field_rec):
        field_object = await object_registry.resolve_async(field_rec)
        field_view = await view_producer.produce_view(field_rec, field_object)
        label = QtGui.QLabel(field_id)
        label.setBuddy(field_view)
        layout.addWidget(label)
        layout.addWidget(field_view)
        layout.addSpacing(10)
        return field_view


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._object_registry = services.object_registry
        self._view_producer = services.view_producer
        services.view_producer_registry.register_view_producer(self._produce_view)

    async def _produce_view(self, type_ref, object, observer):
        if not isinstance(object, RecordObject):
            raise NotApplicable(object)
        return (await RecordView.make(self._object_registry, self._view_producer, object))
