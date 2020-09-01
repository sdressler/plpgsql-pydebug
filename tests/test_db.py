
import pytest

import psycopg2

from lib.db import DB


TEST_DSN = 'postgresql://postgres:1234@blabla.com/somedb'


@pytest.fixture
def cursor_mock(mocker):
    def _wrapper(dbmock_obj, execute_side_effect=None):
        cursor_mock = mocker.MagicMock()
        cursor_mock.execute = mocker.MagicMock(side_effect=execute_side_effect)
        dbmock_obj._conn.cursor.return_value.__enter__.return_value = cursor_mock
        return cursor_mock

    return _wrapper


@pytest.fixture
def dbmock(mocker):
    class DBMock(DB):
        def __init__(self):
            mocker.patch('lib.db.DB._get_conn')
            mocker.patch('lib.db.DB._async_conn_wait')
            super().__init__(TEST_DSN, is_async=False)

    return DBMock()


def test_try_load_extension(mocker, dbmock):
    exit_mock = mocker.patch('sys.exit')
    get_sql_mock = mocker.patch('lib.db.DB.run_sql',
                                side_effect=psycopg2.errors.UndefinedFile)
    dbmock.try_load_extension()
    get_sql_mock.assert_called_with('CREATE EXTENSION IF NOT EXISTS pldbgapi')
    exit_mock.assert_called_with(1)


def test_get_conn_sync(mocker):
    conn_mock = mocker.patch('psycopg2.connect')
    conn = DB._get_conn(TEST_DSN, False)
    conn_mock.assert_called_with(TEST_DSN, async_=False)
    assert conn.autocommit


def test_get_conn_async(mocker):
    conn_mock = mocker.patch('psycopg2.connect')
    conn_wait_mock = mocker.patch('lib.db.DB._async_conn_wait')
    conn = DB._get_conn(TEST_DSN, True)
    conn_mock.assert_called_with(TEST_DSN, async_=True)
    conn_wait_mock.assert_called_with(conn)


def test_get_conn_fail(mocker):
    exit_mock = mocker.patch('sys.exit')
    conn_mock = mocker.patch('psycopg2.connect', side_effect=psycopg2.OperationalError)
    DB._get_conn(TEST_DSN, False)
    exit_mock.assert_called_with(1)


def test_cleanup(mocker, dbmock):
    dbmock.cleanup()
    dbmock._conn.close.assert_called()


def test_run_sql(dbmock, cursor_mock):
    cursor_mock = cursor_mock(dbmock)
    dbmock.run_sql('SELECT 1')
    cursor_mock.execute.assert_called_with('SELECT 1')


def test_run_sql_fetch_result(dbmock, cursor_mock):
    cursor_mock = cursor_mock(dbmock)
    dbmock.run_sql('SELECT 1', fetch_result=True)
    cursor_mock.execute.assert_called_with('SELECT 1')
    cursor_mock.fetchall.assert_called_once()


@pytest.mark.parametrize('error', [
    psycopg2.errors.SyntaxError,
    psycopg2.errors.ConnectionFailure,
])
def test_run_sql_errors(mocker, dbmock, cursor_mock, error):
    log_exception_mock = mocker.patch('loguru.logger.exception')
    cursor_mock = cursor_mock(dbmock, execute_side_effect=error)
    dbmock.run_sql('Hello World')
    log_exception_mock.assert_called_once()


def test_send_notices(mocker, dbmock):
    TEST_NOTICES = [1, 3, 2]

    queue_mock = mocker.MagicMock()
    dbmock._conn.notices = TEST_NOTICES
    DB._send_notices(dbmock._conn, queue_mock)

    # Not so ideal, makes assumptions about the implementation
    queue_mock.put_nowait.assert_has_calls([mocker.call(x) for x in TEST_NOTICES])

    assert not dbmock._conn.notices
