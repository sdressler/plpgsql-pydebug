
import os

from glob import glob

import psycopg2
import pytest

from lib.debugger import Debugger


DSN = 'postgresql://postgres:password@localhost/test_plpgsql_pydebug'


def _execute_sql(dsn, sql):
    conn = psycopg2.connect(dsn)
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(sql)

    conn.close()


def _execute_sql_no_db(dsn, sql):
    dsn, _, _ = dsn.rpartition('/')
    _execute_sql(dsn, sql)


@pytest.fixture(scope="session")
def debugger_instance():
    dsn = DSN

    _execute_sql_no_db(dsn, 'DROP DATABASE IF EXISTS test_plpgsql_pydebug')
    _execute_sql_no_db(dsn, 'CREATE DATABASE test_plpgsql_pydebug')

    sql_path = os.path.join('tests', 'integration', 'sql', '*')
    for sql_file_path in glob(sql_path):
        with open(sql_file_path, 'r') as sql_file:
            sql = sql_file.read()
            _execute_sql(dsn, sql)

    debugger = Debugger(dsn)
    yield debugger

    # Teardown code from here on
    debugger.stop_debug_session()
    debugger.database.cleanup()
    _execute_sql_no_db(dsn, 'DROP DATABASE test_plpgsql_pydebug')
