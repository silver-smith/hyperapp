import sys
import token, tokenize
from io import BytesIO
import ply.lex as lex
import ply.yacc as yacc
from .htypes import (
    tTypeDef,
    t_named,
    t_field_meta,
    t_optional_meta,
    t_list_meta,
    t_hierarchy_class_meta,
    t_command_meta,
    t_interface_meta,
    TypeRegistry,
    )


keywords = ['opt', 'list', 'class', 'interface', 'list_interface', 'commands', 'columns']

BLOCK_BEGIN = 'BLOCK_BEGIN'
BLOCK_END = 'BLOCK_END'
ARROW = 'ARROW'
tok_name = dict(token.tok_name,
                ENCODING='ENCODING')

NEWLINE = tok_name[token.NEWLINE]
NL = tok_name[tokenize.NL]

ignored_tokens = [NL]

token_types = [
    tokenize.ENCODING,
    token.ENDMARKER,
    token.NEWLINE,
    token.NAME,
    token.EQUAL,
    token.LPAR,
    token.RPAR,
    token.COLON,
    token.COMMA,
    ]

EXACT_TOKEN_TYPES = {
    '->':  ARROW,
    }
tokens = [tok_name[t] for t in token_types] + [
    BLOCK_BEGIN,
    BLOCK_END,
    ARROW,
    ] + [keyword.upper() for keyword in keywords]


def register_typedef( parser, name, type ):
    typedef = tTypeDef(name=name, type=type)
    t = parser.meta_registry.resolve(parser.type_registry, typedef.type)
    parser.type_registry.register(typedef.name, t)
    return typedef

def syntax_error( p, token_num, msg ):
    line_num = p.lineno(token_num)
    print(p.parser.lines[line_num - 1])
    print('%s:%d: %s' % (p.parser.fname, line_num, msg))
    raise SyntaxError(msg)


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

def p_typedef_1( p ):
    'typedef : NAME EQUAL type_expr'
    p[0] = register_typedef(p.parser, p[1], p[3])

def p_typedef_2( p ):
    'typedef : NAME EQUAL class_def'
    p[0] = register_typedef(p.parser, p[1], p[3])

def p_typedef_3( p ):
    'typedef : NAME EQUAL interface_def'
    p[0] = register_typedef(p.parser, p[1], p[3])


def p_class_def( p ):
    'class_def : NAME CLASS NAME class_base_def class_fields_def'
    p[0] = t_hierarchy_class_meta(p[1], p[3], p[4], p[5])

def p_class_base_def_1( p ):
    'class_base_def : LPAR NAME RPAR'
    p[0] = p[2]

def p_class_base_def_2( p ):
    'class_base_def : empty'
    p[0] = None


def p_class_fields_def_1( p ):
    'class_fields_def : COLON NEWLINE BLOCK_BEGIN field_list BLOCK_END'
    p[0] = p[4]
    
def p_class_fields_def_2( p ):
    'class_fields_def : empty'
    p[0] = []


def p_interface_def( p ):
    'interface_def : INTERFACE NAME COLON NEWLINE BLOCK_BEGIN interface_command_defs BLOCK_END'
    p[0] = t_interface_meta(p[2], p[6])

def p_list_interface_def( p ):
    'interface_def : LIST_INTERFACE NAME COLON NEWLINE BLOCK_BEGIN interface_columns_defs interface_command_defs BLOCK_END'
    p[0] = t_interface_meta(p[2], p[7])

def p_interface_command_defs( p ):
    'interface_command_defs : COMMANDS COLON NEWLINE BLOCK_BEGIN interface_command_list BLOCK_END'
    p[0] = p[5]

def p_interface_command_list_1( p ):
    'interface_command_list : interface_command_list NEWLINE interface_command'
    p[0] = p[1] + [p[3]]

def p_interface_command_list_3( p ):
    'interface_command_list : interface_command'
    p[0] = [p[1]]

def p_interface_command( p ):
    'interface_command : NAME NAME LPAR command_field_list RPAR ARROW LPAR command_field_list RPAR'
    p[0] = t_command_meta(p[1], p[2], p[4], p[8])

def p_command_field_list_1( p ):
    'command_field_list : command_field_list COMMA command_field'
    p[0] = p[1] + [p[3]]

def p_command_field_list_2( p ):
    'command_field_list : command_field'
    p[0] = [p[1]]

def p_command_field_list_3( p ):
    'command_field_list : empty'
    p[0] = []

def p_command_field( p ):
    'command_field : NAME COLON type_expr'
    p[0] = t_field_meta(p[1], p[3])


def p_interface_columns_defs( p ):
    'interface_columns_defs : COLUMNS COLON NEWLINE BLOCK_BEGIN columns_defs BLOCK_END NEWLINE'
    p[0] = p[5]


def p_columns_defs_1( p ):
    'columns_defs : columns_defs NEWLINE column_def'
    p[0] = p[1] + [p[3]]

    
def p_columns_defs_2( p ):
    'columns_defs : column_def'
    p[0] = [p[1]]


def p_column_def( p ):
    'column_def : NAME COLON type_expr'


def p_field_list_1( p ):
    'field_list : field_list NEWLINE field_def'
    p[0] = p[1] + [p[3]]

def p_field_list_2( p ):
    'field_list : field_def'
    p[0] = [p[1]]

def p_field_def( p ):
    'field_def : NAME COLON type_expr'
    p[0] = t_field_meta(p[1], p[3])


def p_type_expr_1( p ):
    'type_expr : NAME'
    name = p[1]
    if not p.parser.type_registry.has_name(name):
        syntax_error(p, 1, 'Unknown name: %r' % name)
    p[0] = t_named(name)

def p_type_expr_2( p ):
    'type_expr : type_expr OPT'
    p[0] = t_optional_meta(p[1])

def p_type_expr_3( p ):
    'type_expr : type_expr LIST'
    p[0] = t_list_meta(p[1])


def p_empty( p ):
    'empty :'
    pass


class Lexer(object):

    def input( self, input ):
        self._tokenizer = tokenize.tokenize(BytesIO(input.encode('utf-8')).readline)
        self._tab_size = None
        self._indent = 0
        self._next_token = None  # looked-ahead

    def token( self ):
        if self._next_token:
            tok = self._next_token
        else:
            tok = self._get_next_token()
        if not tok:
            return tok
        while True:
            next = self._get_next_token()
            if not next or not next.type in ignored_tokens:
                break
        if tok.type == NEWLINE and next and next.type == BLOCK_END:
            tok, next = next, tok  # swap NEWLINE and BLOCK_END - parser is straightforward then
        self._next_token = next
        return tok

    def _get_next_token( self ):
        try:
            tinfo = self._tokenizer.__next__()
        except StopIteration:
            return None
        if tinfo.type == token.INDENT:
            if not self._tab_size:
                # first indent found, this is file tab size
                assert '\t' not in tinfo.string, 'Tab intention is not supported'
                self._tab_size = len(tinfo.string)
            assert len(tinfo.string) % self._tab_size == 0, \
              'line %d: Invalid indent: %r (detected tab size: %d)' % (tinfo.start[0], tinfo.string, self._tab_size)
            assert len(tinfo.string)/self._tab_size == self._indent + 1, 'Invalid indent: %r (detected tab size: %d)' % (tinfo.string, self._tab_size)
            self._indent += 1
            t = BLOCK_BEGIN
        elif tinfo.type == token.DEDENT:
            self._indent -= 1
            t = BLOCK_END
        elif tinfo.type == token.OP and tinfo.string in EXACT_TOKEN_TYPES:
            t = EXACT_TOKEN_TYPES[tinfo.string]
        elif tinfo.string in keywords:
            t = tinfo.string.upper()
        else:
            t = tok_name[tinfo.exact_type]
        ## print('Lexer.token', t, tinfo)
        tok = lex.LexToken()
        tok.type = t
        tok.value = tinfo.string
        tok.lineno = tinfo.start[0]
        tok.lexpos = tinfo.start[1]
        return tok


def parse_type_module( meta_registry, type_registry, fname, contents, debug=False ):
    parser = yacc.yacc(debug=debug)
    parser.fname = fname
    parser.lines = contents.splitlines()
    parser.meta_registry = meta_registry
    parser.type_registry = TypeRegistry(next=type_registry)
    typedefs = parser.parse(contents, lexer=Lexer())
    return (typedefs, parser.type_registry)
 

if __name__ == '__main__':
    main()
