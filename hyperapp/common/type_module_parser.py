import sys
import token, tokenize
from io import BytesIO
import ply.lex as lex
import ply.yacc as yacc
from .htypes import t_named, tTypeDef


ENCODING = tokenize.ENCODING
BLOCK_BEGIN = 'BLOCK_BEGIN'
BLOCK_END = 'BLOCK_END'
tok_name = dict(token.tok_name,
                ENCODING='ENCODING')

token_types = [
    ENCODING,
    token.ENDMARKER,
    token.NEWLINE,
    token.NAME,
    token.EQUAL,
    ]

tokens = [tok_name[t] for t in token_types] + [
    BLOCK_BEGIN,
    BLOCK_END,
    ]    


def p_module( p ):
    'module : ENCODING typedef_list eom'
    p[0] = p[2]

def p_eom_1( p ):
    'eom : NEWLINE ENDMARKER'

def p_eom_2( p ):
    'eom : ENDMARKER'

def p_typedef_list_1( p ):
    'typedef_list : typedef_list NEWLINE typedef'
    p[0] = p[1] + [p[3]]

def p_typedef_list_2( p ):
    'typedef_list : typedef'
    p[0] = [p[1]]

def p_typedef( p ):
    'typedef : NAME EQUAL type_expr'
    p[0] = tTypeDef(name=p[1], type=p[3])

def p_type_expr_name( p ):
    'type_expr : NAME'
    p[0] = t_named(p[1])


class Lexer(object):

    def input( self, input ):
        self._tokenizer = tokenize.tokenize(BytesIO(input.encode('utf-8')).readline)
        self._tab_size = None
        self._indent = 0

    def token( self ):
        try:
            tinfo = self._tokenizer.__next__()
        except StopIteration:
            return None
        if tinfo.type == token.INDENT:
            if not self._tab_size:
                # first indent found, this is file tab size
                assert '\t' not in tinfo.string, 'Tab intention is not supported'
                self._tab_size = len(tinfo.string)
            assert len(tinfo.string) % self._tab_size == 0, 'Invalid indent: %r (detected tab size: %d)' % (token.string, self._tab_size)
            assert len(tinfo.string)/self._tab_size == 1, 'Invalid indent: %r (detected tab size: %d)' % (token.string, self._tab_size)
            self._indent += 1
            t = BLOCK_BEGIN
        elif tinfo.type == token.DEDENT:
            self._indent -= 1
            t = BLOCK_END
        else:
            t = tok_name[tinfo.exact_type]
        ## print('Lexer.token', t, tinfo)
        tok = lex.LexToken()
        tok.type = t
        tok.value = tinfo.string
        tok.lineno = tinfo.start[0]
        tok.lexpos = tinfo.start[1]
        return tok


def parse_type_module( contents, debug=False ):
    parser = yacc.yacc(debug=debug)
    return parser.parse(contents, lexer=Lexer())
 

if __name__ == '__main__':
    main()
