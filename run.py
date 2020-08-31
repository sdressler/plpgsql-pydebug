#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from sys import stdout

from loguru import logger
from prompt_toolkit import PromptSession

from lib.debugger import Debugger

PROMPT='(pldbg) '


def main(args: Namespace):
    debugger = Debugger(args.dsn)
    session = PromptSession()

    while True:
        try:
            text = session.prompt(PROMPT)
            debugger.execute_command(text)
            if text in ('exit', 'quit'):
                break

        except KeyboardInterrupt:
            print('To exit type "exit", "quit", or hit Ctrl-D\n')
            continue

        except (EOFError, Exception):
            debugger.execute_command('abort')
            break

if __name__ == '__main__':
    args_to_parse = ArgumentParser()
    args_to_parse.add_argument('--dsn', required=True, help=(
        'The DSN of the PostgreSQL database to connect to'))
    args_to_parse.add_argument('--debug', action='store_true', help=(
        'Show debug messages'))
    args = args_to_parse.parse_args()

    logger.remove()
    logger.add(stdout, level='DEBUG' if args.debug else 'INFO')

    main(args)
