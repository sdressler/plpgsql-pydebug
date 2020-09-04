
from collections import namedtuple
from typing import List, Optional

from loguru import logger

from lib.db import DB


SQLFunction = namedtuple('SQLFunction', ['name', 'oid'])


def get_all_functions(database: DB) -> List[SQLFunction]:
    '''
    Cache all PL/pgSQL functions and their OIDs.
    '''
    logger.info('Caching all PL/pgSQL functions')
    pgsql_functions = database.run_sql('''
        SELECT
            p.oid::regprocedure AS name
          , p.oid AS oid
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        JOIN pg_language l ON p.prolang = l.oid
        WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
          AND l.lanname = 'plpgsql'
    ''', fetch_result=True)
    return [SQLFunction(name, oid) for name, oid in pgsql_functions]


def get_func_oid_by_name(database, func_name) -> Optional[int]:
    '''
    Takes a function name and returns the matching OID. Currently does not
    work for overloaded functions.
    '''
    sql_functions = get_all_functions(database)
    for item in sql_functions:
        if func_name == item.name.partition('(')[0]:
            return item.oid

    return None
