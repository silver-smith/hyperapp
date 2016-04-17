from hyperapp.common.htypes import tObject, tBaseObject
from ..objimpl_registry import objimpl_registry
from ..object import Object
from ..command import Command
from ..import form_view
from .controller import identity_controller


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
        return [Command('submit', 'Create', 'Create new identity, generate private+public key pair', 'Return')]

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'submit':
            return self.run_command_submit(initiator_view, **kw)
        return Object.run_command(self, command_id, initiator_view, **kw)

    def run_command_submit( self, initiator_view, name ):
        print 'creating identity %r...' % name
        identity_controller.generate(name)
        print 'creating identity %r: done' % name


def make_identity_form():
    return form_view.Handle(IdentityFormObject(), [
        form_view.Field('name', form_view.StringFieldHandle('anonymous')),
        ])


objimpl_registry.register('identity_form', IdentityFormObject.from_data)
