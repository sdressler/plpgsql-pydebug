'''
This is the main debugger module. It receives commands to execute and
distributes them accordingly to either the target or the proxy.
'''

from functools import reduce as f_reduce

from loguru import logger

from lib.commands import COMMANDS
from lib.db import DB
from lib.formatters import print_notices
from lib.helpers import get_all_functions
from lib.target import Target
from lib.proxy import Proxy


def rgetattr(obj, attr, *args):
    '''
    Get an attribute recursively. For instance `self.foo.bar` returns `bar`.
    '''
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return f_reduce(_getattr, [obj] + attr.split('.'))


class Debugger:
    '''
    This is the main class for PL/pgSQL debugging.
    '''
    def __init__(self, dsn: str):
        self.database = DB(dsn)
        self.database.try_load_extension()

        self.proxy = None
        self.target = None

    def active_session(self):
        '''
        Check if a debugging session is active or not.
        '''
        return (self.proxy) and (self.target)

    def show_all_functions(self):
        functions = get_all_functions(self.database)
        logger.info(functions)

    def _start_debug_session_wrapper(self, *args):
        func_call = args[0]
        target = Target(self.database.dsn)
        proxy = Proxy(self.database.dsn)
        self._start_debug_session(func_call, target, proxy)

    def _start_debug_session(self, func_call: str, target: Target, proxy: Proxy):
        '''
        Start a new debugging session from scratch.
        '''
        self.target = target
        if not self.target.start(func_call):
            logger.error('Could not start target')
            self.target.cleanup()
            self.target = None
            return

        logger.debug('Started target')

        self.proxy = proxy
        self.proxy.attach(self.target.port)
        logger.debug('Proxy started')

    def stop_debug_session(self):
        '''
        Stop the current debugging session.
        '''
        if self.active_session():
            self.proxy.abort()
            self.target.wait_for_shutdown()
            self.target.cleanup()

        self.proxy = None
        self.target = None

    def _get_source_wrapper(self) -> str:
        '''
        Helper function to get the source for the current target function.
        '''
        return self.proxy.get_source(self.target.oid)

    def _set_breakpoint_wrapper(self, *args):
        '''
        Helper function to set a breakpoint in the current target function.
        '''
        try:
            line_number = args[0]
            result = self.proxy.set_breakpoint(self.target.oid, line_number)
            return result

        # This is not enough here
        except IndexError:
            logger.error('Could not get breakpoint line number.')

    def _run_command(self, command_name, args):
        '''
        Execute a debugging command.
        '''
        if command_name in ('abort', 'exit', 'quit'):
            command_name = 'stop'

        try:
            command = COMMANDS[command_name]['command']

            if command.prereq:
                assert getattr(self, command.prereq)()

            func = rgetattr(self, command.func)
            logger.debug(f'Calling {func} with {args}')
            result = func(*args)

            if command.return_func:
                command.return_func(result)

        except KeyError:
            logger.error(f'Cannot find definition for "{command_name}"')


    def execute_command(self, command, args):
        '''
        Parse and execute a given command.
        '''
        logger.debug(f'Executing: {command} with args {args}')
        self._run_command(command, args)

        if self.active_session():
            print_notices(self.target.get_notices())
