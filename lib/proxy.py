
from collections import namedtuple
from typing import Tuple, Any, List

from loguru import logger

from lib.db import DB


Breakpoint = namedtuple('Breakpoint', ['oid', 'line', 'func'])
Frame = namedtuple('Frame', ['call_count', 'target_name', 'oid', 'line', 'args'])
Variable = namedtuple('Variable', ['name', 'var_class', 'line', 'unique', 'const',
                                   'not_null', 'dtype', 'value'])


class Proxy:
    '''
    Contains code to control the target indirectly.
    '''

    def __init__(self, dsn: str):
        self.db = DB(dsn)
        self.session_id = None

    def _run_cmd(self, cmd: str, args: List) -> List:
        args = ','.join([str(arg) for arg in args])
        return self.db.run_sql(f'SELECT * FROM {cmd}({args})', fetch_result=True)

    def attach(self, port: int) -> int:
        result = self._run_cmd('pldbg_attach_to_port', [port])
        self.session_id = result[0][0]

    def cont(self):
        result = self._run_cmd('pldbg_continue', [self.session_id])
        logger.debug(f'Continue result: {result}')

    def abort(self):
        result = self._run_cmd('pldbg_abort_target', [self.session_id])
        logger.debug(f'Abort result: {result}')

    def get_variables(self) -> List[Variable]:
        result = self._run_cmd('pldbg_get_variables', [self.session_id])
        return [Variable(*row) for row in result]

    def step_over(self) -> Breakpoint:
        result = self._run_cmd('pldbg_step_over', [self.session_id])
        return Breakpoint(*result[0])

    def step_into(self) -> Breakpoint:
        result = self._run_cmd('pldbg_step_into', [self.session_id])
        return Breakpoint(*result[0])

    def get_source(self, oid) -> str:
        result = self._run_cmd('pldbg_get_source', [self.session_id, oid])
        return result[0][0]

    def get_stack(self) -> List[Frame]:
        result = self._run_cmd('pldbg_get_stack', [self.session_id])
        return [Frame(*row) for row in result]

    def get_breakpoints(self) -> List[Breakpoint]:
        result = self._run_cmd('pldbg_get_breakpoints', [self.session_id])
        return [Breakpoint(*row) for row in result]

    def set_breakpoint(self, oid, line_number):
        result = self._run_cmd('pldbg_set_breakpoint', [self.session_id, oid, line_number])
        logger.debug(f'Set breakpoint result: {result}')
