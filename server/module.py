from object import Command, ObjectBase


class ModuleCommand(Command):

    def __init__( self, id, text, desc, shortcut, module_name ):
        Command.__init__(self, id, text, desc, shortcut)
        self.module_name = module_name

    def as_json( self ):
        return dict(Command.as_json(self),
                    module_name=self.module_name)


# base class for modules
class Module(ObjectBase):

    module_registry = []
    module_by_name = {}

    def __init__( self, name ):
        ObjectBase.__init__(self)
        self.name = name
        self.module_registry.append(self)  # preserves import order
        self.module_by_name[name] = self

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
    def run_resolve( cls, path ):
        module = path['module']
        return cls.module_by_name[module].resolve(path)

    def resolve( self, path ):
        return self

    def get_commands( self ):
        return []

    @classmethod
    def get_all_modules_commands( cls ):
        commands = []
        for module in cls.module_registry:
            commands += module.get_commands()
        return commands
    
    def make_path( self, **kw ):
        return dict(module=self.name, **kw)
