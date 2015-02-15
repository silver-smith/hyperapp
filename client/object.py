

class Object(object):

    def get_title( self ):
        raise NotImplementedError(self.__class__)

    def get_commands( self ):
        raise NotImplementedError(self.__class__)

    def run_command( self, command_id ):
        raise NotImplementedError(self.__class__)
