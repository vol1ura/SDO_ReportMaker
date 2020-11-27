from time import sleep

if __name__ == '__name__':
    import sys


def mymes(mes: str, d: float, plus_mark=True):
    """
    Information output to console. If plus_mark is False then the ending plus is not typing.
    :param mes: str
    :param d: float
    :param plus_mark: bool
    """
    k = 80 - len(mes) - 7
    print(mes + '...', end='')
    for i in range(k):
        print('.', end='')
        sleep(d / k)
    if plus_mark:
        print('.[+]')
    else:
        print('....')
