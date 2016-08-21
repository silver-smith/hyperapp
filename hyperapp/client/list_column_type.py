import abc



def register_column_types( registry, services ):
    registry.register('string', StringColumnType.from_state)
    registry.register('int', IntColumnType.from_state)
    registry.register('date_type', DateTimeColumnType.from_state)


class ColumnType(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def to_string( self, value ):
        pass


class SimpleColumnType(ColumnType):

    @classmethod
    def from_state( cls, state ):
        return cls()


class StringColumnType(SimpleColumnType):

#    type = tString

    def to_string( self, value ):
        return value


class IntColumnType(SimpleColumnType):

#    type = tInt

    def to_string( self, value ):
        return str(value)


class DateTimeColumnType(SimpleColumnType):

#    type = tDateTime

    def to_string( self, value ):
        return dt2local_str(value)

