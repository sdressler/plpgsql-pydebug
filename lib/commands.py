

from collections import namedtuple, OrderedDict
from pprint import pprint
from typing import Generator, List, Tuple

from loguru import logger
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completer, Completion, CompleteEvent

from lib.formatters import print_source


Command = namedtuple('Command', ['func', 'prereq', 'return_func'])


COMMANDS = OrderedDict({
    'brshow': {
        'command': Command('proxy.get_breakpoints', 'active_session', pprint),
        'help': 'Show all breakpoints'
    },
    'brset': {
        'command': Command('_set_breakpoint_wrapper', 'active_session', None),
        'help': 'Set a breakpoint'
    },
    'continue': {
        'command': Command('proxy.cont', 'active_session', None),
        'help': 'Continue until the next breakpoint'
    },
    'exit': {
        'help': 'Exit the debugger'
    },
    'func': {
        'command': Command('show_all_functions', None, None),
        'help': 'Show all functions'
    },
    'help': {
        'help': 'Show help'
    },
    'run': {
        'command': Command('_start_debug_session_wrapper', None, None),
        'help': 'Run a function call and attach'
    },
    'si': {
        'command': Command('proxy.step_into', 'active_session', logger.info),
        'help': 'Step into the next function or pause at the next executable statement'
    },
    'so': {
        'command': Command('proxy.step_over', 'active_session', logger.info),
        'help': 'Step over the next function and pause at the next executable statement'
    },
    'source': {
        'command': Command('_get_source_wrapper', 'active_session', print_source),
        'help': 'Show the source of the current active function'
    },
    'stack': {
        'command': Command('proxy.get_stack', 'active_session', pprint),
        'help': 'Show the current stack'
    },
    'stop': {
        'command': Command('stop_debug_session', None, None),
        'help': 'Stop debugging the current active target'
    },
    'vars': {
        'command': Command('proxy.get_variables', 'active_session', pprint),
        'help': 'Show variables of the current frame'
    },
})


def parse_command(command: str) -> Tuple[str,List]:
    command, _, args = command.partition(' ')

    args = args.split(' ')
    if args == ['']:
        args = []

    return command, args


class CommandCompleter(Completer):
    def __init__(self):
        self.command_keys = list(COMMANDS.keys())

    def get_completions(self, document: Document,
                        complete_event: CompleteEvent) -> Generator[Completion, None, None]:
        check = document.text
        matches = [key for key in self.command_keys if key.startswith(check)]
        for match in matches:
            meta_text = COMMANDS[match]['help']
            position = document.cursor_position
            yield Completion(match, start_position=-position, display_meta=meta_text)
