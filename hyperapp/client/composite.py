# composite component - base class

from . import view


class Handle(view.Handle):

    def get_child_handle( self ):
        raise NotImplementedError(self.__class__)

    def get_object( self ):
        return self.get_child_handle().get_object()

    def get_title( self ):
        return self.get_child_handle().get_title()

    def map_current( self, mapper ):
        raise NotImplementedError(self.__class__)


class Composite(view.View):
    pass
