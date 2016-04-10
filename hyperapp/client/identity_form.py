from ..common.htypes import tObject, tBaseObject
from .objimpl_registry import objimpl_registry
from . object import Object
from . import form_view


tIdentityFormObject = tObject.register('identity_form', base=tBaseObject)


class IdentityFormObject(Object):

    @classmethod
    def from_data( cls, data, server=None ):
        return IdentityFormObject()

    def get_title( self ):
        return 'Create identity'

    def to_data( self ):
        return tIdentityFormObject.instantiate('identity_form')

    def get_commands( self ):
        return []


def make_identity_form():
    return form_view.Handle(IdentityFormObject(), [
        form_view.Field('name', form_view.StringFieldHandle('anonymous')),
        ])


objimpl_registry.register('identity_form', IdentityFormObject.from_data)
