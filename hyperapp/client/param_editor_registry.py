import asyncio
from .command_class import Command
from .registry import Registry


class ParamEditorOpenCommand(Command):

    def __init__( self, id, kind, resource_id, is_default_command, enabled, object_wr, args=None ):
        #assert isinstance(object_wr(), ProxyObject), repr(object_wr)
        Command.__init__(self, id, kind, resource_id, is_default_command, enabled)
        self._object_wr = object_wr
        self._args = args or ()

    def __repr__( self ):
        return 'ParamEditorOpenCommand(%r)' % self.id

    def get_view( self ):
        return None

    def clone( self, args=None ):
        args = self._args + (args or ())
        return ParamEditorOpenCommand(self.id, self.kind, self.resource_id, self.is_default_command, self.enabled, self._object_wr, args)

    @asyncio.coroutine
    def run( self, *args, **kw ):
        object = self._object_wr()
        if not object: return
        assert 0  # todo


class ParamEditorRegistry(Registry):

    def resolve( self, state ):
        pass
