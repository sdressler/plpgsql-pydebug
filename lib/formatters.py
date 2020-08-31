
from typing import List


def print_source(src: str):
    for index, line in enumerate(src.split('\n')):
        line_number = index + 1
        print(f'{line_number:3}: {line}')


def print_notices(notices: List[str]):
    for notice in notices:
        print(notice.strip())
