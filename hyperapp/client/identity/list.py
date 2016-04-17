from hyperapp.common.htypes import (
    tString,
    tBaseObject,
    list_handle_type,
    Column,
    )
from ..objimpl_registry import objimpl_registry
from ..list_object import Element, Slice, ListObject
from .. import list_view
from .controller import IdentityItem, IdentityController, identity_controller


identity_list_type = tBaseObject
identity_list_handle_type = list_handle_type('identity_list', tString)


class IdentityList(ListObject):

    @classmethod
    def from_data( cls, objinfo, server=None ):
        return cls(identity_controller)
    
    def __init__( self, controller ):
        assert isinstance(controller, IdentityController), repr(controller)
        ListObject.__init__(self)
        self.controller = controller

    def get_title( self ):
        return 'Identity list'

    def get_commands( self ):
        return []

    def to_data( self ):
        return identity_list_type.instantiate('identity_list')

    def get_columns( self ):
        return [
            Column('name', 'Identity name'),
            ]

    def get_key_column_id( self ):
        return 'name'

    def fetch_elements( self, sort_column_id, key, desc_count, asc_count ):
        self._notify_fetch_result(self._get_slice())

    def _get_slice( self ):
        items = self.controller.get_items()
        return Slice('name', None, 'asc', map(self._item2element, items), bof=True, eof=True)

    def _item2element( self, item ):
        assert isinstance(item, IdentityItem), repr(item)
        return Element(item.name, item, commands=[])


def make_identity_list( key=None ):
    object = IdentityList(identity_controller)
    return list_view.Handle(identity_list_handle_type, object, sort_column_id='name', key=key)


objimpl_registry.register('identity_list', IdentityList.from_data)
