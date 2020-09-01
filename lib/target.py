'''
This module controls the debugging target. It is responsible for setting the
initial breakpoint and starting the function to be debugged.
'''

from collections import namedtuple
from queue import Queue
from threading import Thread
from typing import List, Optional, Tuple

from loguru import logger
from psycopg2.errors import QueryCanceled

from lib.db import DB


SQLFunction = namedtuple('SQLFunction', ['name', 'oid'])


class Target:
    '''
    This is the target. It controls/contains the code to be debugged.
    '''
    def __init__(self, dsn: str):
        self.database = DB(dsn, is_async=True)
        self.notice_queue = Queue()
        self.oid = None
        self.executor = None
        self.port = None

    def cleanup(self):
        '''
        Cleanup routine for the target.
        '''
        self.database.cleanup()

    def get_notices(self) -> List[str]:
        '''
        Get all notices the target might have. Reads from an internal queue,
        does not use the DB itself since it is likely blocked.
        '''
        notices = []
        while not self.notice_queue.empty():
            notices.append(self.notice_queue.get())
        logger.debug(f'Target notices: {notices}')
        return notices

    @classmethod
    def _parse_port(cls, port_raw: str) -> int:
        return int(port_raw.split(':')[-1])

    def wait_for_shutdown(self):
        '''
        Wait until the target completed fully.
        '''
        self.executor.join()

    def start(self, func_call: str) -> bool:
        '''
        Start target debugging. Resolve the function to be debugged, find its
        OID and eventually start a thread calling it.
        '''
        if '(' not in func_call or ')' not in func_call:
            logger.error(f'Function call seems incomplete: {func_call}')
            return False

        func_name, func_args = Target._parse_func_call(func_call)
        func_oid = self._get_func_oid_by_name(func_name)
        if not func_oid:
            logger.error('Function OID not found. Either function is not '
                         'defined or there are multiple with the same name '
                         'which is currently not support')
            return False

        logger.debug(f'Function OID is: {func_oid}')

        self.executor = Thread(target=self._run, args=(func_call, func_oid))
        self.executor.daemon = True
        self.executor.start()

        # Wait here until the executor started
        logger.debug('Waiting for port')
        self.port = Target._parse_port(self.notice_queue.get())
        logger.debug(f'Port is: {self.port}')

        return True

    def _run(self, func_call: str, func_oid: int):
        '''
        Start a debugging session. Consumes the function call to debug with its
        arguments and returns the session ID once the debugger started.
        '''
        self.oid = func_oid
        self.database.run_sql(f'SELECT * FROM pldbg_oid_debug({func_oid})')

        while True:
            logger.debug('Starting target function')

            try:
                result = self.database.run_sql(f'SELECT * FROM {func_call}',
                                         fetch_result=True,
                                         notice_queue=self.notice_queue)

                # This will now wait here until the function finishes. It will
                # eventually restart immediately. Otherwise, the proxy process
                # hangs until it hits a timeout.

                logger.debug(f'Target result: {result}')

            except QueryCanceled:
                logger.info('Stopped target query')
                break


    @classmethod
    def _parse_func_call(cls, func_call: str) -> Tuple[str, List[str]]:
        '''
        Take a function call and return the function name and its arguments.
        '''
        func_call = func_call.replace(' ', '').replace('(', ',').replace(')', '')
        func_call = func_call.split(',')
        return func_call[0], func_call[1:]

    def _get_func_oid_by_name(self, func_name) -> Optional[int]:
        '''
        Takes a function name and returns the matching OID. Currently does not
        work for overloaded functions.
        '''
        sql_functions = self._get_all_functions()
        for item in sql_functions:
            if func_name == item.name.partition('(')[0]:
                return item.oid

        return None

    def _get_all_functions(self) -> List[SQLFunction]:
        '''
        Cache all PL/pgSQL functions and their OIDs.
        '''
        logger.info('Caching all PL/pgSQL functions')
        pgsql_functions = self.database.run_sql('''
            SELECT
                p.oid::regprocedure AS name
              , p.oid AS oid
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            JOIN pg_language l ON p.prolang = l.oid
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND l.lanname = 'plpgsql'
        ''', fetch_result=True)
        return [SQLFunction(name, oid) for name, oid in pgsql_functions]
