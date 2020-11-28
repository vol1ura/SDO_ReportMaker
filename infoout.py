from colorama import init, Fore
from time import sleep
import sys

# if __name__ == '__name__':

init(autoreset=True)


def mymes(mes: str, d: float, plus_mark=True):
    """
    Information output to console. If plus_mark is False then the ending plus is not typing.
    :param mes: str
    :param d: float
    :param plus_mark: bool
    """
    k = 80 - len(mes) - 6
    print(mes + '...', end='')
    for i in range(k):
        print('.', end='')
        sleep(d / k)
    if plus_mark:
        print(Fore.GREEN + '[+]')
    else:
        print('...')


def getsettings():
    try:
        with open('settings.txt') as f:
            s = f.readlines()
    except(IOError, OSError) as e:
        print(e)
        print()
        sys.exit(Fore.RED + 'Error when reading sdo.auth file!!!')
    return s
