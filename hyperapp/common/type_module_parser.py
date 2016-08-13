import sys
import token, tokenize
from io import BytesIO
import ply.lex as lex
import ply.yacc as yacc
from .htypes import t_named, tTypeDef


ENCODING = tokenize.ENCODING
tok_name = dict(token.tok_name,
                ENCODING='ENCODING')

token_types = [
    ENCODING,
    token.ENDMARKER,
    token.NEWLINE,
    token.NAME,
    token.EQUAL,
    ]

tokens = [tok_name[t] for t in token_types]


def p_module_1( p ):
    'module : ENCODING typedef_list eom'
    p[0] = p[2]

def p_eom_1( p ):
    'eom : NEWLINE ENDMARKER'

def p_eom_2( p ):
    'eom : ENDMARKER'

def p_typedef_list_multi( p ):
    'typedef_list : typedef_list NEWLINE typedef'
    p[0] = p[1] + [p[3]]

def p_typedef_list_single( p ):
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

    def token( self ):
        try:
            tinfo = self._tokenizer.__next__()
        except StopIteration:
            return None
        t = tok_name[tinfo.exact_type]
        print('Lexer.token', t, tinfo)
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
