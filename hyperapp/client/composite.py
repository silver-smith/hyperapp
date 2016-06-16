# composite component - base class

from ..common.util import flatten
from . import view


## class Handle(view.Handle):

##     def __init__( self, children ):
##         self.children = children

##     def get_child_handle( self ):
##         raise NotImplementedError(self.__class__)

##     def get_object( self ):
##         return self.get_child_handle().get_object()

##     def get_title( self ):
##         return self.get_child_handle().get_title()

##     def get_module_ids( self ):
##         return flatten(child.get_module_ids() for child in self.children)
        
##     def map_current( self, mapper ):
##         raise NotImplementedError(self.__class__)


class Composite(view.View):
    pass
