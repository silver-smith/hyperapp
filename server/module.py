from object import Command


class ModuleCommand(Command):

    def __init__( self, id, text, desc, shortcut, module_name ):
        Command.__init__(self, id, text, desc, shortcut)
        self.module_name = module_name

    def as_json( self ):
        return dict(Command.as_json(self),
                    module_name=self.module_name)


# base class for modules
class Module(object):

    module_registry = []
    module_by_name = {}

    def __init__( self, name ):
        self.name = name
        self.module_registry.append(self)
        self.module_by_name[name] = self

    def init_phase2( self ):
        pass

    @classmethod
    def run_phase2_init( cls ):
        for module in cls.module_registry:
            module.init_phase2()

    def get_commands( self ):
        return []

    @classmethod
    def get_all_modules_commands( cls ):
        commands = []
        for module in cls.module_registry:
            commands += module.get_commands()
        return commands
    
