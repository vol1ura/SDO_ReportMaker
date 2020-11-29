import csv
from datetime import datetime

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


def readfiledata(file_date: datetime):
    table = []
    fieldnames = ['s_time', 'pair_n', 'group', 'group_n', 'type', 'discipline', 'forum', 'journal']
    f_name = 'sdoweek_' + file_date.strftime("%d_%m_%y") + '.csv'
    with open(f_name, 'r', newline='', encoding='utf8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames)
        for row in reader:
            table.append(row)
    for row in table:
        row['time'] = datetime.strptime(row['s_time'], '%Y-%m-%d %H:%M:%S')
        del row['s_time']
    return table
