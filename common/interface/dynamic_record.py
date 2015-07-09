from . types import join_path, Type, TString, Field, TRecord


class TDynamicRec(TRecord):

    def __init__( self, fields, base=None ):
        TRecord.__init__(self, fields, base=base)

    # must return TRecord
    def resolve_dynamic( self, fixed_rec ):
        raise NotImplementedError(self.__class__)

    def instantiate( self, *args, **kw ):
        fixed_rec = self.instantiate_impl(args, kw, check_unexpected=False)
        t = self.resolve_dynamic(fixed_rec)
        return t.instantiate(*args, **kw)
