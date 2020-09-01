'''
This module is responsible for handling connections to the database. It takes
care of connecting, disconnecting and executing SQL statements. It can make use
of asynchronous connections.
'''

import select
import sys

from queue import Queue
from typing import Optional

import psycopg2

from loguru import logger


class DB:
    '''
    Helper class to make DB access more easy.
    '''

    def __init__(self, dsn, is_async: bool = False):
        self.dsn = dsn
        self._conn = DB._get_conn(dsn, is_async)
        self.pid = self._conn.get_backend_pid()

    def try_load_extension(self):
        '''
        Tries to load the `pldbgapi` extension. Exits with 1 if it fails.
        '''
        try:
            logger.info('Loading pldbgapi')
            self.run_sql('CREATE EXTENSION IF NOT EXISTS pldbgapi')

        except psycopg2.errors.UndefinedFile:
            logger.error('Could not load the extension. Is pldbgapi installed?')
            sys.exit(1)

    @classmethod
    def _get_conn(cls, dsn: str, is_async: bool) -> object:
        '''
        Return a psycopg2 connection for the given dsn. The connection can be
        asynchronous.
        '''
        try:
            conn = psycopg2.connect(dsn, async_=is_async)
            if is_async:
                DB._async_conn_wait(conn)

            if not is_async:
                conn.autocommit = True

            return conn

        except psycopg2.OperationalError:
            logger.exception('Could not connect to database.')
            sys.exit(1)

    def cleanup(self):
        '''
        Cleanup procedure for the DB module.
        '''
        self._conn.close()

    def run_sql(self, sql: str, fetch_result: bool = False,
                notice_queue: Optional[Queue] = None) -> Optional[list]:
        '''
        Execute a piece of SQL. Can optionally return the result. For
        asynchronous connections, it takes a Queue to return statements
        generated while the query blocks.
        '''
        # import pdb
        # pdb.set_trace()
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql)
                if self._conn.async_:
                    DB._async_conn_wait(self._conn, notice_queue=notice_queue)

                if fetch_result:
                    return cur.fetchall()

                return []

        except psycopg2.errors.SyntaxError:
            logger.exception('SQL invalid')
            return []

        except psycopg2.errors.ConnectionFailure:
            logger.exception('Connection failure')
            return []

    @classmethod
    def _send_notices(cls, async_conn, notice_queue: Optional[Queue]):
        '''
        Handler to capture all notices from the current connection. Pushes it
        into the provided queue. If the Queue is None, this function silently
        returns. The connections notices are cleared at the end.
        '''
        if not notice_queue:
            return

        for notice in async_conn.notices:
            notice_queue.put_nowait(notice)

        # Clear notices
        async_conn.notices = []

    @classmethod
    def _async_conn_wait(cls, async_conn, notice_queue: Optional[Queue] = None):
        '''
        Wait for an asynchronous connection. It will push all notices of the
        connection into the supplied queue, if it is not None.
        '''
        while True:
            state = async_conn.poll()
            if state == psycopg2.extensions.POLL_OK:
                cls._send_notices(async_conn, notice_queue)
                break

            if state == psycopg2.extensions.POLL_WRITE:
                cls._send_notices(async_conn, notice_queue)
                select.select([], [async_conn.fileno()], [])

            elif state == psycopg2.extensions.POLL_READ:
                cls._send_notices(async_conn, notice_queue)
                select.select([async_conn.fileno()], [], [])

            else:
                raise psycopg2.OperationalError(f'poll() returned unhandled state {state}')
