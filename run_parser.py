#!/usr/bin/env python3

import logging
import argparse
from hyperapp.common.htypes import TList, tTypeDef
from hyperapp.common.visual_rep import pprint
from hyperapp.common.type_module_parser import Lexer, parse_type_module


def test_lex( fpaths ):
    for fpath in fpaths:
        print('%s:' % fpath)
        lexer = Lexer()
        with open(fpath) as f:
            input = f.read()
        lexer.input(input)
        while True:
            tok = lexer.token()
            print(tok)
            if not tok:
                break

def test_yacc( fpaths ):
    for fpath in fpaths:
        print('%s:' % fpath)
        with open(fpath) as f:
            input = f.read()
        print('parsing:')
        result = parse_type_module(input, debug=True)
        print('result:', result)
        pprint(TList(tTypeDef), result)


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
