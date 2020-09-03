
import pytest

from lib.commands import parse_command


@pytest.mark.parametrize('full_command,exp_command,exp_args', [
    ('dosomething', 'dosomething', []),
    ('a bla', 'a', ['bla']),
    ('b.a arg arg', 'b.a', ['arg', 'arg']),
])
def test_parse_command(full_command, exp_command, exp_args):
    command, args = parse_command(full_command)
    assert command == exp_command
    assert args == exp_args
