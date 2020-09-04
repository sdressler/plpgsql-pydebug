
import pytest

from psycopg2.errors import QueryCanceled

import lib.helpers as lib_helpers

from lib.helpers import SQLFunction
from lib.target import Target


@pytest.fixture
def target_fixture(mocker):
    class TargetFixture(Target):
        mocker.patch('lib.db.DB')

        def __init__(self):
            super().__init__('postgresql://postgres@ajhkoafs.com/testdb')
            self.database = mocker.MagicMock()

    return TargetFixture()


def test_cleanup(target_fixture):
    target_fixture.cleanup()
    target_fixture.database.cleanup.assert_called_once()


def test_get_notices(target_fixture):
    NOTICES = ['a', 'b', 'c']
    for x in NOTICES:
        target_fixture.notice_queue.put_nowait(x)
    assert target_fixture.get_notices() == NOTICES


def test_parse_port():
    port = Target._parse_port('abc:123')
    assert port == 123


def test_wait_for_shutdown(mocker, target_fixture):
    target_fixture.executor = mocker.MagicMock()
    target_fixture.wait_for_shutdown()
    target_fixture.executor.join.assert_called_once()


@pytest.mark.parametrize('func_call, func_name, func_args', [
    ('foobar(arg1, arg2)', 'foobar', ['arg1', 'arg2']),
    ('foobar (arg1, arg2)', 'foobar', ['arg1', 'arg2']),
    ('foobar()', 'foobar', ['']),
])
def test_parse_func_call(func_call, func_name, func_args):
    name, args = Target._parse_func_call(func_call)
    assert name == func_name
    assert args == func_args


@pytest.mark.parametrize('call,result', [
    ('foobar', False),
    ('foobar(', False),
    ('foobar)', False),
    ('foobar()', True),
    ('()', False),
    ('foobar(123, 456)', True),
    ('foo_bar(arg)', True),
    ('foo_bar_baz(3)', True),
    ('example_func_1(2)', True),
])
def test_assert_valid_function_call(call, result):
    assert Target.assert_valid_function_call(call) == result


def test_start_invalid_func(target_fixture):
    assert not target_fixture.start('GARBAGE')


def test_start_no_func_oid(mocker, target_fixture):
    mocker.patch('lib.target.get_func_oid_by_name', return_value=None)
    assert not target_fixture.start('some_valid_call(bla)')


def test_start_valid_func(mocker, target_fixture):
    mocker.patch('lib.target.get_func_oid_by_name', return_value=100)
    target_fixture.notice_queue.get = mocker.MagicMock(return_value='FOO: 42')
    target_fixture._run_executor_thread = mocker.MagicMock()

    assert target_fixture.start('func_call(arg)')


def test_run(mocker, target_fixture):
    side_effects = [None, 'foo', QueryCanceled]
    target_fixture.database.run_sql.side_effect = iter(side_effects)
    target_fixture._run('hello_world(2,3)', 123)

    target_fixture.database.run_sql.assert_has_calls([
        mocker.call('SELECT * FROM pldbg_oid_debug(123)'),
        mocker.call('SELECT * FROM hello_world(2,3)',
                    fetch_result=True,
                    notice_queue=target_fixture.notice_queue),
        mocker.call('SELECT * FROM hello_world(2,3)',
                    fetch_result=True,
                    notice_queue=target_fixture.notice_queue)
    ])
