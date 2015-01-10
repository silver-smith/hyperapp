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
    def get_object( cls, path ):
        module = path['module']
        return cls.module_by_name[module].resolve(path)

    def resolve( self, path ):
        assert False, repr(path)  # 404 Not found

    def get_commands( self ):
        return []

    @classmethod
    def get_all_modules_commands( cls ):
        commands = []
        for module in cls.module_registry:
            commands += module.get_commands()
        return commands
    
    @classmethod
    def run_module_command( cls, module_name, command_id ):
        module = cls.module_by_name[module_name]
        return module.run_command(command_id)

    def make_path( self, **kw ):
        return dict(module=self.name, **kw)
