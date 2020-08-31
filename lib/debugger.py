
import sys

from collections import namedtuple
from functools import reduce as f_reduce
from pprint import pprint
from threading import Thread, Event
from typing import List, Optional, Tuple

from loguru import logger

from lib.db import DB
from lib.formatters import print_source, print_notices
from lib.target import Target
from lib.proxy import Proxy


Command = namedtuple('Command', ['func', 'prereq', 'return_func'])


COMMANDS = {
    'run'     : Command('start_debug_session', None, None),
    'stop'    : Command('stop_debug_session', None, None),
    'continue': Command('proxy.cont', 'active_session', None),
    'vars'    : Command('proxy.get_variables', 'active_session', pprint),
    'si'      : Command('proxy.step_into', 'active_session', print),
    'so'      : Command('proxy.step_over', 'active_session', print),
    'source'  : Command('_get_source_wrapper', 'active_session', print_source),
    'stack'   : Command('proxy.get_stack', 'active_session', pprint),
    'br.show' : Command('proxy.get_breakpoints', 'active_session', pprint),
    'br.set'  : Command('_set_breakpoint_wrapper', 'active_session', None),
}


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return f_reduce(_getattr, [obj] + attr.split('.'))


class Debugger:
    '''
    This is the main class for PL/pgSQL debugging.
    '''
    def __init__(self, dsn: str):
        self.db = DB(dsn)
        self.db.try_load_extension()

        self.proxy = None
        self.target = None

    def active_session(self):
        return (self.proxy) and (self.target)

    def start_debug_session(self, *args):
        func_call = args[0]

        self.target = Target(self.db.dsn)
        if not self.target.start(func_call):
            logger.error('Could not start target')
            self.target.cleanup()
            self.target = None
            return

        logger.debug('Started target')

        self.proxy = Proxy(self.db.dsn)
        self.proxy.attach(self.target.port)
        logger.debug('Proxy started')

    def stop_debug_session(self):
        if self.active_session():
            self.proxy.abort()
            self.target.wait_for_shutdown()
            self.target.cleanup()

        self.proxy = None
        self.target = None

    def _get_source_wrapper(self) -> str:
        return self.proxy.get_source(self.target.oid)

    def _set_breakpoint_wrapper(self, *args):
        try:
            line_number = args[0]
            return self.proxy.set_breakpoint(self.target.oid, line_number)

        except IndexError:
            logger.error('Could not get breakpoint line number.')

    def _run_command(self, command_name, args):
        if command_name in ('abort', 'exit', 'quit'):
            command_name = 'stop'

        try:
            command = COMMANDS[command_name]

            if command.prereq:
                assert getattr(self, command.prereq)()

            func = rgetattr(self, command.func)
            logger.debug(f'Calling {func} with {args}')
            result = func(*args)

            if command.return_func:
                command.return_func(result)

        except KeyError:
            logger.error(f'Cannot find definition for "{command_name}"')

    def execute_command(self, command):
        '''
        Parse and execute a given command.
        '''
        logger.debug(f'Executing: {command}')
        command, _, args = command.partition(' ')

        args = args.split(' ')
        if args == ['']:
            args = []

        self._run_command(command, args)

        if self.active_session():
            print_notices(self.target.get_notices())
