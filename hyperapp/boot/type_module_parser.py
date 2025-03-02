import sys
import token, tokenize
from collections import namedtuple
from io import BytesIO

import ply.lex as lex
import ply.yacc as yacc

from .htypes import (
    name_mt,
    field_mt,
    optional_mt,
    list_mt,
    record_mt,
    exception_mt,
    )


class ParseError(Exception):
    pass


TypeDef = namedtuple('TypeDef', 'name type')
TypeImport = namedtuple('TypeImport', 'module_name source_name target_name')
TypeModule = namedtuple('TypeModule', 'module_name import_list typedefs')


# class SimpleMtGenerator:

#     def __init__(self, mt):
#         self._mt = mt

#     def generate(self, module_name=None, name=None):
#         return self._mt


class RecordMtGenerator:

    def __init__(self, t, base, fields):
        self._t = t
        self._base = base
        self._fields = fields

    def generate(self, module_name, name):
        return self._t(module_name, name, self._base, self._fields)
    

keywords = [
    'import',
    'as',
    'from',
    'opt',
    'list',
    'record',
    'exception',
    'list_service_type',
    ]

STMT_SEP = 'STMT_SEP'  # NEWLINEs converted to this one
BLOCK_BEGIN = 'BLOCK_BEGIN'
BLOCK_END = 'BLOCK_END'
ARROW = 'ARROW'
tok_name = dict(token.tok_name,
                ENCODING='ENCODING')

NEWLINE = tok_name[token.NEWLINE]
NL = tok_name[tokenize.NL]
ENDMARKER = tok_name[token.ENDMARKER]
COMMENT = tok_name[tokenize.COMMENT]


class Grammar:

    _token_types = [
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

    def __init__(self, keywords):
        self.tokens = [tok_name[t] for t in self._token_types] + [
            STMT_SEP,
            BLOCK_BEGIN,
            BLOCK_END,
            ARROW,
            ] + [keyword.upper() for keyword in keywords]

    def _syntax_error(self, p, token_num, msg):
        line_num = p.lineno(token_num)
        p.parser.error_line = p.parser.lines[line_num - 1]
        p.parser.error = '{}:{}: {}'.format(p.parser.fname, line_num, msg)
        raise SyntaxError(msg)

    def _unknown_name_error(self, p, token_num, name):
        self._syntax_error(p, token_num, 'Unknown name: %r' % name)

    # grammar =======================================================================================

    def p_module(self, p):
        'module : ENCODING module_contents ENDMARKER'
        p[0] = p[2]

    def p_module_contents_1(self, p):
        'module_contents : import_list STMT_SEP typedef_list'
        p[0] = TypeModule(
            module_name=p.parser.module_name,
            import_list=p[1],
            typedefs=p[3],
            )

    def p_module_contents_2(self, p):
        'module_contents : typedef_list_opt'
        p[0] = TypeModule(
            module_name=p.parser.module_name,
            import_list=[],
            typedefs=p[1],
            )


    def p_import_list_1(self, p):
        'import_list : import_list STMT_SEP import_def'
        p[0] = p[1] + p[3]

    def p_import_list_2(self, p):
        'import_list : import_def'
        p[0] = p[1]


    def p_import_def_list(self, p):
        'import_def : FROM NAME IMPORT name_list'
        p[0] = [TypeImport(p[2], source_name=name, target_name=name) for name in p[4]]
        p.parser.known_name_set |= set(p[4])

    def p_import_def_as(self, p):
        'import_def : FROM NAME IMPORT NAME AS NAME'
        p[0] = [TypeImport(p[2], source_name=p[4], target_name=p[6])]
        p.parser.known_name_set.add(p[6])

    def p_name_list_1(self, p):
        'name_list : NAME'
        p[0] = [p[1]]

    def p_name_list_2(self, p):
        'name_list : name_list COMMA NAME'
        p[0] = p[1] + [p[3]]


    def p_typedef_list_opt_1(self, p):
        'typedef_list_opt : empty'
        p[0] = []

    def p_typedef_list_opt_2(self, p):
        'typedef_list_opt : typedef_list'
        p[0] = p[1]

    def p_typedef_list_1(self, p):
        'typedef_list : typedef_list STMT_SEP typedef'
        p[0] = p[1] + [p[3]]

    def p_typedef_list_2(self, p):
        'typedef_list : typedef'
        p[0] = [p[1]]

    def p_typedef(self, p):
        'typedef : NAME EQUAL typedef_rhs'
        p[0] = TypeDef(name=p[1], type=p[3])
        p.parser.known_name_set.add(p[1])

    def p_typedef_rhs_expr(self, p):
        'typedef_rhs : type_expr'
        p[0] = p[1]

    def p_typedef_rhs_record(self, p):
        'typedef_rhs : record_def'
        p[0] = p[1]

    def p_typedef_rhs_exception(self, p):
        'typedef_rhs : exception_def'
        p[0] = p[1]


    def p_record_def_1(self, p):
        'record_def : RECORD record_base_name_def'
        base_name = p[2]
        if base_name:
            base_mt = name_mt(base_name)
            base_ref = p.parser.mosaic.put(base_mt)
        else:
            base_ref = None
        p[0] = RecordMtGenerator(record_mt, base_ref, ())

    def p_record_def_2(self, p):
        'record_def : RECORD record_base_name_def COLON BLOCK_BEGIN field_list BLOCK_END'
        base_name = p[2]
        if base_name:
            base = p.parser.mosaic.put(name_mt(base_name))
        else:
            base = None
        p[0] = RecordMtGenerator(record_mt, base, tuple(p[5]))

    def p_record_base_name_def_1(self, p):
        'record_base_name_def : empty'
        p[0] = None

    def p_record_base_name_def_2(self, p):
        'record_base_name_def : LPAR NAME RPAR'
        p[0] = p[2]


    def p_exception_def_1(self, p):
        'exception_def : EXCEPTION exception_base_name_def'
        base_name = p[2]
        if base_name:
            base_mt = name_mt(base_name)
            base_ref = p.parser.mosaic.put(base_mt)
        else:
            base_ref = None
        p[0] = RecordMtGenerator(exception_mt, base_ref, ())

    def p_exception_def_2(self, p):
        'exception_def : EXCEPTION exception_base_name_def COLON BLOCK_BEGIN field_list BLOCK_END'
        base_name = p[2]
        if base_name:
            base = p.parser.mosaic.put(name_mt(base_name))
        else:
            base = None
        p[0] = RecordMtGenerator(exception_mt, base, tuple(p[5]))

    def p_exception_base_name_def_1(self, p):
        'exception_base_name_def : empty'
        p[0] = None

    def p_exception_base_name_def_2(self, p):
        'exception_base_name_def : LPAR NAME RPAR'
        p[0] = p[2]


    def p_field_list_1(self, p):
        'field_list : field_list STMT_SEP field_def'
        p[0] = p[1] + [p[3]]

    def p_field_list_2(self, p):
        'field_list : field_def'
        p[0] = [p[1]]

    def p_field_def(self, p):
        'field_def : NAME COLON type_expr'
        ref = p.parser.mosaic.put(p[3])
        p[0] = field_mt(p[1], ref)


    def p_type_expr_1(self, p):
        'type_expr : NAME'
        name = p[1]
        if not name in p.parser.known_name_set:
            self._unknown_name_error(p, 1, name)
        p[0] = name_mt(name)

    def p_type_expr_2(self, p):
        'type_expr : type_expr OPT'
        base_t = p.parser.mosaic.put(p[1])
        p[0] = optional_mt(base_t)

    def p_type_expr_3(self, p):
        'type_expr : type_expr LIST'
        element_t = p.parser.mosaic.put(p[1])
        p[0] = list_mt(element_t)


    def p_empty(self, p):
        'empty :'
        pass


class Lexer:

    _ignored_tokens = [NL, COMMENT]
    _exact_token_types = {
        '->':  ARROW,
        }

    def __init__(self, keywords):
        self._keywords = keywords

    def input(self, input):
        self._tokenizer = tokenize.tokenize(BytesIO(input.encode('utf-8')).readline)
        self._tab_size = None
        self._indent = 0
        self._next_token = None  # looked-ahead

    def token(self):
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
            if not next or not next.type in self._ignored_tokens:
                break
        if tok.type == STMT_SEP and next and next.type == ENDMARKER:
            tok, next = next, None  # remove STMT_SEP before ENDMARKER
        if tok.type == STMT_SEP and next and next.type == BLOCK_BEGIN:
            tok, next = next, None  # remove STMT_SEP before BLOCK_BEGIN
        if tok.type == STMT_SEP and next and next.type == BLOCK_END:
            tok, next = next, tok  # swap STMT_SEP and BLOCK_END - parser is straightforward then
        self._next_token = next
        return tok

    def _get_next_token(self):
        try:
            tinfo = self._tokenizer.__next__()
        except StopIteration:
            return None
        if tinfo.type == token.INDENT:
            if not self._tab_size:
                # first indent found, this is file tab size
                assert '\t' not in tinfo.string, 'Tab indentation is not supported'
                self._tab_size = len(tinfo.string)
            if len(tinfo.string) % self._tab_size != 0:
                raise ParseError('line {}: Invalid indent: {!r} (detected tab size: {})'
                                 .format(tinfo.start[0], tinfo.string, self._tab_size))
            assert len(tinfo.string)/self._tab_size == self._indent + 1, 'Invalid indent: %r (detected tab size: %d)' % (tinfo.string, self._tab_size)
            self._indent += 1
            t = BLOCK_BEGIN
        elif tinfo.type == token.DEDENT:
            self._indent -= 1
            t = BLOCK_END
        elif tinfo.type == token.NEWLINE:
            t = STMT_SEP
        elif tinfo.type == token.OP and tinfo.string in self._exact_token_types:
            t = self._exact_token_types[tinfo.string]
        elif tinfo.string in self._keywords:
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


def parse_type_module_source(builtin_types, mosaic, fname, module_name, contents, debug=False):
    grammar = Grammar(keywords)
    parser = yacc.yacc(debug=debug, module=grammar)
    parser.mosaic = mosaic
    parser.module_name = module_name
    parser.fname = fname
    parser.lines = contents.splitlines()
    parser.known_name_set = set(builtin_types.keys())
    parser.error_line = None
    parser.error = None
    #parser.provided_class_list = []
    lexer = Lexer(keywords)
    try:
        module = parser.parse(contents, lexer=lexer)
    except ParseError as x:
        raise RuntimeError('Failed to parse {}: {}'.format(fname, x))
    if not module:
        raise RuntimeError('Failed to parse {}:\n{}\n{}'.format(fname, parser.error_line, parser.error))
    return module

 
def load_type_module_source(builtin_types, mosaic, fpath, module_name, debug=False):
    contents = fpath.read_text()
    return parse_type_module_source(builtin_types, mosaic, fpath, module_name, contents, debug)
