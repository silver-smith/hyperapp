import logging
from .util import Path

log = logging.getLogger(__name__)


class ModuleCommand(object):

    def __init__( self, id, text, desc, shortcut, module_name ):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.module_name = module_name


# base class for modules
class Module(object):

    module_registry = []
    module_by_name = {}

    def __init__( self, name ):
        self.name = name
        self.module_registry.append(self)  # preserves import order
        self.module_by_name[name] = self
        log.debug('Module.__init__: %s', name)

    def init_phase2( self ):
        pass

    def init_phase3( self ):
        pass

    @classmethod
    def init_phases( cls ):
        for module in cls.module_registry:
            module.init_phase2()
        for module in cls.module_registry:
            module.init_phase3()

    @classmethod
    def get_module_by_name( cls, name ):
        return cls.module_by_name[name]

    @classmethod
    def run_resolver( cls, iface, path ):
        path = Path(path)
        module = path.pop_str()
        return cls.module_by_name[module].resolve(iface, path)

    def resolve( self, iface, path ):
        path.raise_not_found()

    def get_commands( self ):
        return []

    @classmethod
    def get_all_modules_commands( cls ):
        commands = []
        for module in cls.module_registry:
            commands += module.get_commands()
        return commands
    
    def make_path( self, *args ):
        return [self.name] + list(args)
