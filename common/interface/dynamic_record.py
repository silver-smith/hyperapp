from . types import join_path, Type, TString, Field, TRecord


class TDynamicRec(TRecord):

    def __init__( self, fields, base=None ):
        TRecord.__init__(self, fields, base=base)

    # must return TRecord
    def resolve_dynamic( self, fixed_rec ):
        raise NotImplementedError(self.__class__)
