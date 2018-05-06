#!/usr/bin/env python3

import os.path
import logging
import argparse
from hyperapp.common.htypes import (
    TList,
    tTypeDef,
    tTypeModule,
    make_meta_type_registry,
    builtin_type_registry,
    )    
from hyperapp.common.visual_rep import pprint
from hyperapp.common.type_module_parser import Lexer, parse_type_module

log = logging.getLogger(__name__)


def test_lex(fpaths):
    for fpath in fpaths:
        log.info('%s:' % fpath)
        lexer = Lexer()
        with open(fpath) as f:
            input = f.read()
        lexer.input(input)
        while True:
            tok = lexer.token()
            log.info(tok)
            if not tok:
                break

def test_yacc(fpaths):
    builtins = builtin_type_registry()
    for fpath in fpaths:
        log.info('%s:', fpath)
        dir, fname = os.path.split(fpath)
        module_name = os.path.splitext(fname)[0]
        with open(fpath) as f:
            input = f.read()
        log.info('parsing %s:', module_name)
        module = parse_type_module(builtins, module_name, fpath, input, debug=True)
        log.info('%d imports:', len(module.import_list))
        for imp in module.import_list:
            log.info('\t%s.%s', imp.module_name, imp.imported_name)
        log.info('%d typedefs:', len(module.typedefs))
        for typedef in module.typedefs:
            log.info('\t%s: %s', typedef.name, typedef.type)
        pprint(tTypeModule, module)


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')

    parser = argparse.ArgumentParser(description='Hyperapp types file parser test')
    parser.add_argument('command', choices=['lex', 'yacc'], help='What to test')
    parser.add_argument('fpaths', nargs='+', help='Type files to parse')
    args = parser.parse_args()

    if args.command == 'lex':
        test_lex(args.fpaths)
    elif args.command == 'yacc':
        test_yacc(args.fpaths)
    
main()
