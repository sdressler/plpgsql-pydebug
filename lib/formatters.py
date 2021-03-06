
from typing import List, Tuple

from loguru import logger
from prompt_toolkit import print_formatted_text, HTML


def print_help(help: List[Tuple[str, str]]):
    for command, help in help:
        print_formatted_text(HTML(f'<b>{command:8}</b>: {help}'))


def print_source(src: str):
    for index, line in enumerate(src.split('\n')):
        line_number = index + 1
        logger.info('{line_number:3}: {line}')


def print_notices(notices: List[str]):
    for notice in notices:
        logger.info(notice.strip())
