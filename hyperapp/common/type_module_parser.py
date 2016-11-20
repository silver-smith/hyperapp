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
    t_column_meta,
    t_list_interface_meta,
    TypeRegistry,
    TypeResolver,
    )


keywords = ['import', 'from', 'opt', 'list', 'class', 'interface', 'list_interface', 'commands', 'columns', 'contents', 'diff_type']

STMT_SEP = 'STMT_SEP'  # NEWLINEs converted to this one
BLOCK_BEGIN = 'BLOCK_BEGIN'
BLOCK_END = 'BLOCK_END'
ARROW = 'ARROW'
tok_name = dict(token.tok_name,
                ENCODING='ENCODING')

NEWLINE = tok_name[token.NEWLINE]
NL = tok_name[tokenize.NL]
ENDMARKER = tok_name[token.ENDMARKER]

ignored_tokens = [NL]

token_types = [
    tokenize.ENCODING,
    token.ENDMARKER,
    token.NAME,
    token.EQUAL,
    token.LPAR,
    token.RPAR,
    token.COLON,
    token.COMMA,
    token.AT,
    ]

EXACT_TOKEN_TYPES = {
    '->':  ARROW,
    }
tokens = [tok_name[t] for t in token_types] + [
    STMT_SEP,
    BLOCK_BEGIN,
    BLOCK_END,
    ARROW,
    ] + [keyword.upper() for keyword in keywords]


def register_typedef( parser, name, type ):
    typedef = tTypeDef(name=name, type=type)
    t = parser.meta_registry.resolve(parser.resolver, typedef.type)
    parser.new_type_registry.register(typedef.name, t)
    return typedef

def syntax_error( p, token_num, msg ):
    line_num = p.lineno(token_num)
    print(p.parser.lines[line_num - 1])
    print('%s:%d: %s' % (p.parser.fname, line_num, msg))
    raise SyntaxError(msg)


def p_module( p ):
    'module : ENCODING import_list_opt typedef_list_opt ENDMARKER'
    p[0] = (p[2], p[3])


def p_import_list_opt_1( p ):
    'import_list_opt : empty'
    p[0] = []

def p_import_list_opt_2( p ):
    'import_list_opt : import_list'
    p[0] = p[1]

def p_import_list_1( p ):
    'import_list : import_list STMT_SEP import_def'
    p[0] = p[1] + [p[3]]

def p_import_list_2( p ):
    'import_list : import_def'
    p[0] = [p[1]]


def p_import_def( p ):
    'import_def : FROM NAME IMPORT name_list'
    p[0] = [p[2]]

def p_name_list_1( p ):
    'name_list : NAME'
    p[0] = [p[1]]

def p_name_list_2( p ):
    'name_list : name_list COMMA NAME'
    p[0] = p[1] + [p[3]]


def p_typedef_list_opt_1( p ):
    'typedef_list_opt : empty'
    p[0] = []

def p_typedef_list_opt_2( p ):
    'typedef_list_opt : typedef_list'
    p[0] = p[1]

def p_typedef_list_1( p ):
    'typedef_list : typedef_list STMT_SEP typedef'
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
    'class_fields_def : COLON BLOCK_BEGIN field_list BLOCK_END'
    p[0] = p[3]
    
def p_class_fields_def_2( p ):
    'class_fields_def : empty'
    p[0] = []


def p_interface_def_1( p ):
    'interface_def : INTERFACE NAME COLON BLOCK_BEGIN interface_command_defs BLOCK_END'
    p[0] = t_interface_meta(p[2], p[5])

def p_interface_def_2( p ):
    'interface_def : INTERFACE NAME COLON BLOCK_BEGIN interface_contents_defs STMT_SEP interface_command_defs BLOCK_END'
    p[0] = t_interface_meta(p[2], p[7], contents_fields=p[5])

def p_interface_def_3( p ):
    'interface_def : INTERFACE NAME COLON BLOCK_BEGIN interface_diff_type_def STMT_SEP interface_contents_defs STMT_SEP interface_command_defs BLOCK_END'
    p[0] = t_interface_meta(p[2], p[9], contents_fields=p[7], diff_type=p[5])


def p_list_interface_def_1( p ):
    'interface_def : LIST_INTERFACE NAME COLON BLOCK_BEGIN interface_columns_defs STMT_SEP interface_command_defs BLOCK_END'
    p[0] = t_list_interface_meta(p[2], p[7], p[5])

def p_list_interface_def_2( p ):
    'interface_def : LIST_INTERFACE NAME COLON BLOCK_BEGIN interface_columns_defs BLOCK_END'
    p[0] = t_list_interface_meta(p[2], [], p[5])


def p_interface_diff_type_def( p ):
    'interface_diff_type_def : DIFF_TYPE COLON type_expr'
    p[0] = p[3]


def p_interface_contents_defs( p ):
    'interface_contents_defs : CONTENTS COLON BLOCK_BEGIN contents_field_list BLOCK_END'
    p[0] = p[4]

def p_contents_field_list_1( p ):
    'contents_field_list : contents_field_list STMT_SEP contents_field'
    p[0] = p[1] + [p[3]]

def p_contents_field_list_2( p ):
    'contents_field_list : contents_field'
    p[0] = [p[1]]

def p_contents_field( p ):
    'contents_field : NAME COLON type_expr'
    p[0] = t_field_meta(p[1], p[3])


def p_interface_command_defs( p ):
    'interface_command_defs : COMMANDS COLON BLOCK_BEGIN interface_command_list BLOCK_END'
    p[0] = p[4]

def p_interface_command_list_1( p ):
    'interface_command_list : interface_command_list STMT_SEP interface_command'
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
    'interface_columns_defs : COLUMNS COLON BLOCK_BEGIN columns_defs BLOCK_END'
    p[0] = p[4]

def p_columns_defs_1( p ):
    'columns_defs : columns_defs STMT_SEP column_def'
    p[0] = p[1] + [p[3]]

def p_columns_defs_2( p ):
    'columns_defs : column_def'
    p[0] = [p[1]]

def p_column_def_1( p ):
    'column_def : NAME COLON type_expr'
    p[0] = t_column_meta(p[1], p[3], is_key=False)

def p_column_def_2( p ):
    'column_def : AT NAME COLON type_expr'
    p[0] = t_column_meta(p[2], p[4], is_key=True)


def p_field_list_1( p ):
    'field_list : field_list STMT_SEP field_def'
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
    if not p.parser.resolver.has_name(name):
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
            if tok.type == STMT_SEP and next and next.type == STMT_SEP:
                continue  # merge separators
            if not next or not next.type in ignored_tokens:
                break
        if tok.type == STMT_SEP and next and next.type == ENDMARKER:
            tok, next = next, None  # remove STMT_SEP before ENDMARKER
        if tok.type == STMT_SEP and next and next.type == BLOCK_BEGIN:
            tok, next = next, None  # remove STMT_SEP before BLOCK_BEGIN
        if tok.type == STMT_SEP and next and next.type == BLOCK_END:
            tok, next = next, tok  # swap STMT_SEP and BLOCK_END - parser is straightforward then
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
                assert '\t' not in tinfo.string, 'Tab indentation is not supported'
                self._tab_size = len(tinfo.string)
            assert len(tinfo.string) % self._tab_size == 0, \
              'line %d: Invalid indent: %r (detected tab size: %d)' % (tinfo.start[0], tinfo.string, self._tab_size)
            assert len(tinfo.string)/self._tab_size == self._indent + 1, 'Invalid indent: %r (detected tab size: %d)' % (tinfo.string, self._tab_size)
            self._indent += 1
            t = BLOCK_BEGIN
        elif tinfo.type == token.DEDENT:
            self._indent -= 1
            t = BLOCK_END
        elif tinfo.type == token.NEWLINE:
            t = STMT_SEP
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


def parse_type_module( meta_registry, type_registry_registry, fname, contents, debug=False ):
    parser = yacc.yacc(debug=debug)
    parser.fname = fname
    parser.lines = contents.splitlines()
    parser.meta_registry = meta_registry
    parser.imported_type_registry = TypeRegistry()
    parser.new_type_registry = TypeRegistry()
    parser.resolver = TypeResolver([type_registry_registry.resolve_type_registry('builtins'),
                                    parser.imported_type_registry,
                                    parser.new_type_registry])
    used_modules, typedefs = parser.parse(contents, lexer=Lexer())
    return (used_modules, typedefs, parser.new_type_registry)
 

if __name__ == '__main__':
    main()
