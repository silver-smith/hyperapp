import functools
import weakref
from util import is_list_inst, make_action


class ObjKind(object):

    def __init__( self, handle=None ):
        self._handle = handle

    def get_handle( self, args ):
        assert self._handle, 'Not implemented'
        return self._handle

    def matches( self, obj ):
        return False


class Arg(object):

    def __init__( self, name, kind=None ):
        assert kind is None or isinstance(kind, ObjKind), repr(kind)
        self.name = name
        self.kind = kind


# decorator for methods
class command(object):

    registered_commands = {}  # id -> command

    def __init__( self, shortcut, desc, args=None, multi_select=False, enabled=True ):
        assert args is None or is_list_inst(args, (Arg)), repr(args)
        assert shortcut is None or isinstance(shortcut, (basestring, list)), repr(shortcut)
        self.id = None    # set when registered
        self.name = None  # set when registered
        self.args = args or []
        self.shortcut = shortcut
        self.desc = desc
        self.multi_select = multi_select
        self.enabled = enabled
        self.method = None  # set when bound2method
        self.inst = None  # set when bound2inst

    def __getstate__( self ):
        return dict(id=self.id)

    def __setstate__( self, state ):
        self.id = state['id']
        cmd = self.registered_commands.get(self.id)
        if cmd:
            self._copy_attrs(cmd)
        else:
            self.name = self.id.split('.')[-1]
            self.args = []
            self.shortcut = None
            self.desc = 'Command was removed'
            self.multi_select = False
            self.enabled = False
            self.method = lambda: None
        self.inst = None  # todo: pickle/unpickle

    # hidden commands are not registered automatically; they passed argument explicitly
    def is_hidden( self ):
        return self.name.startswith('_')

    def require_explicit_elt_arg( self ):
        return self.is_hidden()

    def required_arg_count( self ):
        count = len(self.args)
        if self.require_explicit_elt_arg():
            count += 1
        return count

    def clone( self ):
        cmd = self.__class__(None, None)
        cmd.id = self.id
        cmd._copy_attrs(self)
        return cmd

    def _copy_attrs( self, src ):
        self.name = src.name
        self.args = src.args
        self.shortcut = src.shortcut
        self.desc = src.desc
        self.multi_select = src.multi_select
        self.enabled = src.enabled
        self.method = src.method

    def is_bound2method( self ):
        return bool(self.method)

    def bind2method( self, method ):
        self.method = method
        self.name = getattr(method, '__name__', None)  # missing for partial
        return self

    def is_bound2inst( self ):
        # python 2.x only; use __self__ in 3.x:
        return self.inst is not None \
          or isinstance(self.method, functools.partial) and self.method.func.im_self is not None \
          or self.method.im_self is not None

    def get_inst( self ):
        if self.inst is not None:
            return self.inst()
        # assume method is not a free function, always a method:
        if isinstance(self.method, functools.partial):
            return self.method.func.im_self
        print self, self.method
        return self.method.im_self

    def bind2instance( self, inst ):
        inst_ref = weakref.ref(inst)
        def bound_method(*args, **kw):
            self_inst = inst_ref()
            assert self_inst, self  # weak-referenced self instance is gone
            return self.method(self_inst, *args, **kw)
        bound_cmd = self.clone()
        ## # following makes 'inst' holded forever by command and never destroyed,
        ## # so had to implement own binding mechanism above
        ## bound_cmd.method = bound_cmd.method.__get__(inst, inst.__class__)
        ## # maybe need to investigate why commands are not freed instead
        bound_cmd.method = bound_method
        bound_cmd.inst = inst_ref
        return bound_cmd

    def __call__( self, method ):
        assert not self.is_bound2method()
        return self.bind2method(method)

    def register( self, name, cls=None, fn=None, id=None ):
        if cls:
            self.id = '%s.%s.%s' % (cls.__module__, cls.__name__, self.name)
        if fn:
            self.bind2method(fn)
        if id:
            self.id = id
        self.name = name
        print '** registering command', repr(self.id)
        self.registered_commands[self.id] = self

    def unregister( self ):
        del self.registered_commands[self.id]

    def add2commands( self, obj ):
        if not self.name.startswith('_'):
            obj._commands.append(self)

    def run( self, *args, **kw ):
        assert self.is_bound2inst()
        return self.method(*args, **kw)

    def make_action( self, w, view_weakref, shortcut, *args, **kw ):
        ## print '--- command.make_action', repr(self.name), repr(self.shortcut), self.inst, args, kw
        ## import traceback; traceback.print_stack()
        def run():
            print '* command/make_action/run', repr(self.name), repr(self.desc), view_weakref, args, kw
            view = view_weakref()
            if view:
                view.run(self, *args, **kw)
        action = make_action(w, self.title(), shortcut, run)
        action.setEnabled(self.enabled)
        w.addAction(action)
        return action

    def title( self ):
        return self.name.strip('_').replace('_', ' ')

    def set_enabled( self, enabled ):
        self.enabled = enabled

    def enable( self ):
        self.set_enabled(True)

    def disable( self ):
        self.set_enabled(False)

    def __repr__( self ):
        return 'command(%r/%r)' % (self.name, self.inst)


class dir_command(command):

    # dir_command for a module always wants explicit dir argument
    def require_explicit_elt_arg( self ):
        return command.require_explicit_elt_arg(self) \
          or isinstance(self.get_inst(), ModuleBase)

    def add2commands( self, obj ):
        #assert issubclass(cls, Dir), repr(cls)
        if not self.is_hidden():
            obj._dir_commands.append(self)

    def __repr__( self ):
        return 'dir_command(%r/%r)' % (self.name, self.inst)


def init_commands( cls, members ):
    for name, member in members.items():
        ## print name, member, isinstance(member, command)
        if isinstance(member, command):
            member.register(name, cls)

# function version - subclasses will not inherit it
# we can not use class version for view.View because views subclass QWidget classes too
# but same metaclass required for all bases
def command_owner_meta_class( name, bases, members ):
    cls = type(name, bases, members)
    init_commands(cls, members)
    return cls


# class version - all subclasses will inherit it
class CommandOwnerMetaClass(type):

    def __new__( meta_cls, name, bases, members ):
        cls = type.__new__(meta_cls, name, bases, members)
        init_commands(cls, members)
        return cls


class CommandOwner(object):

    def _init_commands( self ):
        for name in dir(self):
            attr = getattr(self, name)
            if isinstance(attr, command):
                cmd = attr.bind2instance(self)
                setattr(self, name, cmd)
                cmd.add2commands(self)


class ModuleBase(CommandOwner):
    pass





def collect_objs_commands( objs ):
    #assert objs and is_list_inst(objs, Object), repr(objs)  # empty list disallowed
    commands = objs[0].commands
    cmd_set = set(commands)
    for obj in objs[1:]:
        cmd_set &= set(obj.commands)
    commands = [cmd for cmd in commands if cmd in cmd_set]  # preserve ordering
    if len(objs) > 1:
        commands = [cmd for cmd in commands if cmd.multi_select]
    return commands

def cmd_elements_to_args( cmd, selected_elts ):
    if cmd.multi_select:
        return (selected_elts,)
    else:
        assert len(selected_elts) == 1, repr(selected_elts)
        if cmd.require_explicit_elt_arg():
            return (selected_elts[0],)  # pass element explicitly
        else:
            return ()  # 'self' is enough

def get_dir_commands( dir ):
#    return dir.get_dir_commands() + Module.get_dir_commands(dir)
    return dir.get_dir_commands()
