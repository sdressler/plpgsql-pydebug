
import pytest

from lib.debugger import Debugger


@pytest.fixture
def debugger_fixture(mocker):
    mocker.patch('lib.db.DB')
    class DebuggerFixture(Debugger):
        def __init__(self):
            super().__init__('postgresql://postgres@joidqwjo.com/foobardb')
            self.database = mocker.MagicMock()

    return DebuggerFixture()


@pytest.fixture
def debugger_fixture_active(mocker, debugger_fixture):
    debugger_fixture.target = mocker.MagicMock()
    debugger_fixture.proxy = mocker.MagicMock()
    return debugger_fixture


def test_active_session(mocker, debugger_fixture):
    assert not debugger_fixture.active_session()

    debugger_fixture.proxy = mocker.Mock()
    assert not debugger_fixture.active_session()

    debugger_fixture.target = mocker.Mock()
    assert debugger_fixture.active_session()


def test_start_debug_session(mocker, debugger_fixture):
    target_mock = mocker.MagicMock()
    proxy_mock = mocker.MagicMock()

    debugger_fixture._start_debug_session('some_func', target_mock, proxy_mock)

    target_mock.start.assert_called_once_with('some_func')
    proxy_mock.attach.assert_called_once_with(target_mock.port)

    assert debugger_fixture.target == target_mock
    assert debugger_fixture.proxy == proxy_mock
    assert debugger_fixture.active_session()


def test_start_debug_session_failure(mocker, debugger_fixture):
    target_mock = mocker.MagicMock()
    target_mock.start.return_value = False
    proxy_mock = mocker.MagicMock()

    debugger_fixture._start_debug_session('some_func', target_mock, proxy_mock)

    target_mock.start.assert_called_once_with('some_func')
    proxy_mock.attach.assert_not_called()

    assert not debugger_fixture.target
    assert not debugger_fixture.proxy
    assert not debugger_fixture.active_session()


def test_stop_debug_session(mocker, debugger_fixture_active):
    target_mock = debugger_fixture_active.target
    proxy_mock = debugger_fixture_active.proxy
    debugger_fixture_active.stop_debug_session()

    proxy_mock.abort.assert_called_once()
    target_mock.wait_for_shutdown.assert_called_once()
    target_mock.cleanup.assert_called_once()

    assert not debugger_fixture_active.target
    assert not debugger_fixture_active.proxy
    assert not debugger_fixture_active.active_session()


def test_get_source_wrapper(mocker, debugger_fixture_active):
    TEST_SOURCE = '1\n2\n3\n'

    debugger_fixture_active.target.oid = 42
    debugger_fixture_active.proxy.get_source.return_value = TEST_SOURCE

    source = debugger_fixture_active._get_source_wrapper()

    assert source == TEST_SOURCE
    debugger_fixture_active.proxy.get_source.assert_called_once_with(42)


def test_set_breakpoint_wrapper(debugger_fixture_active):
    debugger_fixture_active.target.oid = 42
    debugger_fixture_active._set_breakpoint_wrapper(100)
    debugger_fixture_active.proxy.set_breakpoint.assert_called_once_with(42, 100)


def test_set_breakpoint_wrapper(mocker, debugger_fixture_active):
    log_error_mock = mocker.patch('loguru.logger.error')
    debugger_fixture_active._set_breakpoint_wrapper()
    log_error_mock.assert_called_once()


def test_run_command(debugger_fixture_active):
    debugger_fixture_active._run_command('vars', [])
    debugger_fixture_active.proxy.get_variables.assert_called_once()


def test_run_command_failure(mocker, debugger_fixture_active):
    log_error_mock = mocker.patch('loguru.logger.error')
    debugger_fixture_active._run_command('klhasfassdashklas', [])
    log_error_mock.assert_called_once()
