
import pytest


from lib.proxy import Proxy, Variable, Frame, Breakpoint


SESSION_ID = 42


@pytest.fixture
def proxy_fixture_impl(mocker):
    mocker.patch('lib.db.DB')

    class ProxyFixture(Proxy):
        def __init__(self, mock_run_cmd, mock_db):
            super().__init__('some dsn')
            self.session_id = SESSION_ID
            if mock_run_cmd:
                self._run_cmd = mocker.MagicMock()

            if mock_db:
                self.database = mocker.MagicMock()

    def _proxy_fixture_wrapper(mock_run_cmd, mock_db):
        return ProxyFixture(mock_run_cmd, mock_db)

    return _proxy_fixture_wrapper


@pytest.fixture
def proxy_fixture(proxy_fixture_impl):
    return proxy_fixture_impl(True, False)


@pytest.fixture
def proxy_fixture_real_run(proxy_fixture_impl):
    return proxy_fixture_impl(False, True)


def test_attach(proxy_fixture):
    proxy_fixture._run_cmd.return_value = [(SESSION_ID + 1,)]
    proxy_fixture.attach(123)

    proxy_fixture._run_cmd.assert_called_once_with('pldbg_attach_to_port', [123])
    assert proxy_fixture.session_id == SESSION_ID + 1


def test_cont(proxy_fixture):
    proxy_fixture.cont()
    proxy_fixture._run_cmd.assert_called_once_with('pldbg_continue', [SESSION_ID])


def test_abort(proxy_fixture):
    proxy_fixture.abort()
    proxy_fixture._run_cmd.assert_called_once_with('pldbg_abort_target', [SESSION_ID])


def test_get_variables(proxy_fixture):
    proxy_fixture._run_cmd.return_value = []
    retval = proxy_fixture.get_variables()

    proxy_fixture._run_cmd.assert_called_once_with('pldbg_get_variables', [SESSION_ID])
    assert retval == []

    VARS = [
        ('a', 'a', 1, False, False, False, 123, 'bla'),
        ('a', 'a', 1, False, False, False, 123, 'bla'),
    ]
    proxy_fixture._run_cmd.return_value = VARS

    retval = proxy_fixture.get_variables()
    assert retval == [Variable(*x) for x in VARS]


def test_step_over(proxy_fixture):
    BPOINT = [(123, 456, 'blaa')]
    proxy_fixture._run_cmd.return_value = BPOINT
    retval = proxy_fixture.step_over()

    proxy_fixture._run_cmd.assert_called_once_with('pldbg_step_over', [SESSION_ID])
    assert retval == Breakpoint(*BPOINT[0])


def test_step_into(proxy_fixture):
    BPOINT = [(123, 456, 'blaa')]
    proxy_fixture._run_cmd.return_value = BPOINT
    retval = proxy_fixture.step_into()

    proxy_fixture._run_cmd.assert_called_once_with('pldbg_step_into', [SESSION_ID])
    assert retval == Breakpoint(*BPOINT[0])


def test_get_source(proxy_fixture):
    SOURCE = 'abc\ndef'
    proxy_fixture._run_cmd.return_value = [(SOURCE,)]
    retval = proxy_fixture.get_source(123)

    proxy_fixture._run_cmd.assert_called_once_with('pldbg_get_source', [SESSION_ID, 123])
    assert retval == SOURCE


def test_get_stack(proxy_fixture):
    FRAME = [
        (1, 'foo', 123, 44, 'something'),
        (2, 'bla', 321, 11, 'else')
    ]
    proxy_fixture._run_cmd.return_value = FRAME
    retval = proxy_fixture.get_stack()

    proxy_fixture._run_cmd.assert_called_once_with('pldbg_get_stack', [SESSION_ID])
    assert retval == [Frame(*x) for x in FRAME]


def test_get_breakpoints(proxy_fixture):
    BPOINTS = [
        (123, 456, 'blaa'),
        (4124123, 456, 'bldaslkljasl'),
    ]
    proxy_fixture._run_cmd.return_value = BPOINTS
    retval = proxy_fixture.get_breakpoints()

    proxy_fixture._run_cmd.assert_called_once_with('pldbg_get_breakpoints', [SESSION_ID])
    assert retval == [Breakpoint(*x) for x in BPOINTS]


def test_set_breakpoint(proxy_fixture):
    proxy_fixture.set_breakpoint(123, 456)
    proxy_fixture._run_cmd.assert_called_once_with('pldbg_set_breakpoint', [SESSION_ID, 123, 456])


def test_run_cmd(mocker, proxy_fixture_real_run):
    ARGS = [1, 2, 3]
    proxy_fixture_real_run._run_cmd('foobar', ARGS)
    proxy_fixture_real_run.database.run_sql.assert_called_once_with(
        f'SELECT * FROM foobar(1,2,3)', fetch_result=True)
