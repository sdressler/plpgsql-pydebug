
import json

from collections import namedtuple

from lib.commands import parse_command
from lib.helpers import get_func_oid_by_name


CommandToTest = namedtuple('CommandToTest', ['command', 'output'])


def test_example_func_1(debugger_instance):
    func_oid = get_func_oid_by_name(debugger_instance.database, 'example_func_1')
    sequence = [
        CommandToTest('run example_func_1(2)', [
            'Caching all PL/pgSQL functions',
            'Caching all PL/pgSQL functions'
        ]),
        CommandToTest('si', [[func_oid, 7, 'example_func_1(integer)']]),
        CommandToTest('continue', [
            'NOTICE:  Iteration: 1',
            'NOTICE:  To go: 1',
            'NOTICE:  Iteration: 2',
            'NOTICE:  To go: 0'
        ]),
        CommandToTest('stop', ['Stopped target query'])
    ]

    expected_output = []
    for item in sequence:
        expected_output.extend(item.output)
        command, args = parse_command(item.command)
        debugger_instance.execute_command(command, args)

    debugger_instance.log_sink.seek(0)

    output = debugger_instance.log_sink.getvalue().split('\n')
    output = [json.loads(x) for x in output if x]
    output = [item['record']['message'] for item in output
        if item['record']['level']['name'] == 'INFO']

    assert output == expected_output
