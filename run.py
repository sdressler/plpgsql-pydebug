#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from sys import stdout

from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from lib.debugger import Debugger
from lib.commands import COMMANDS, CommandCompleter, parse_command
from lib.formatters import print_help


PROMPT='(pldbg) '


def main(args: Namespace):
    completer = CommandCompleter()
    debugger = Debugger(args.dsn)
    session = PromptSession()

    while True:
        try:
            text = session.prompt(PROMPT, completer=completer,
                                  auto_suggest=AutoSuggestFromHistory())

            if text in ('exit', 'quit'):
                break

            elif text in ('help', 'h', '?'):
                print_help(COMMANDS.help)

            else:
                command, args = parse_command(text)

                if command not in completer.command_keys:
                    logger.error(f'Command {text} not found.')
                    continue

                debugger.execute_command(command, args)

        except KeyboardInterrupt:
            print('To exit type "exit", "quit", or hit Ctrl-D\n')
            continue

        except EOFError:
            logger.info('Exiting.')
            debugger.execute_command('abort')
            break

        except Exception:
            logger.exception('That was unexpected.')


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
