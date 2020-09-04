
import pytest

import lib.helpers as lib_helpers

from lib.helpers import SQLFunction


@pytest.mark.parametrize('func_name,oid', [
    ('foobar', 1),
    ('match', 42),
    ('does_not_exist', None)
])
def test_func_oid_by_name(mocker, func_name, oid):
    mocker.patch.object(lib_helpers, 'get_all_functions', return_value=[
        SQLFunction('foobar(integer)', 1),
        SQLFunction('foobar(varchar)', 2),
        SQLFunction('match(integer, text)', 42)
    ])
    assert lib_helpers.get_func_oid_by_name(mocker.MagicMock(), func_name) == oid


def test_get_all_functions(mocker):
    database = mocker.MagicMock()
    database.run_sql.return_value = [('func1', 1), ('func2', 2)]

    all_functions = lib_helpers.get_all_functions(database)
    assert all_functions == [
        SQLFunction('func1', 1),
        SQLFunction('func2', 2)
    ]
