from colorama import init, Fore
import csv
from datetime import datetime
import sys
from time import sleep

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


def getsettings(f_name: str):
    """
    Function for reading settings files and get data as list of strings.

    :param f_name: str
    :return: list
    """
    try:
        with open(f_name) as f:
            s = f.readlines()
    except(IOError, OSError) as e:
        print(e)
        print()
        sys.exit(Fore.RED + 'Error when reading ' + f_name + ' file!')
    return s


def readfiledata(file_date: datetime):
    """
    Function returns collected data from teacher's timetable and list of courses on sdo.rgsu.net
    It is used for transfer data from one module to another.
    Parameter file_date is a begin of week for which we run modules.

    :param file_date: datetime
    :return: list
    """
    table = []
    fieldnames = ['row', 's_time', 'pair_n', 'group', 'group_n', 'type', 'discipline', 'forum', 'journal']
    f_name = 'sdoweek_' + file_date.strftime("%d_%m_%y") + '.csv'
    try:
        with open(f_name, 'r', newline='', encoding='utf8') as f:
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                table.append(row)
    except(IOError, OSError) as e:
        print(e)
        print()
        sys.exit(Fore.RED + 'Error when reading ' + f_name + '! Check also file encoding.')
    for row in table:
        row['time'] = datetime.strptime(row['s_time'], '%Y-%m-%d %H:%M:%S')
        del row['s_time']
    print('File ' + Fore.CYAN + f_name + Fore.WHITE + ' was imported' +
          '.' * (80 - len(f_name) - 21) + Fore.GREEN + '[+]')
    return table
