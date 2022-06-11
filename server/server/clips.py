import re
import logging

_default_clips = (
    'consiglio_magico',
    'paolocannone',
    'benson'
)

def default(command):
    match = re.search('command/([0-9]+)', command)
    if match is not None:
        n = int(match.group(1))
        if n < len(_default_clips):
            return _default_clips[n]
        raise IndexError(f'Could\'t find clip number {n}')
    else:
        logging.warning(f'Message didn\'t match: {command}')
