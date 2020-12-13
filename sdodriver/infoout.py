from colorama import init, Fore
from datetime import datetime
import pickle
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


def get_settings(f_name: str):
    """
    Function for reading settings files and get data as list of strings.

    :param f_name: str
    :return: list
    """
    try:
        with open(f_name, encoding='utf8') as f:
            s = f.readlines()
    except(IOError, OSError) as e:
        print(e)
        print()
        sys.exit(Fore.RED + f'Error when reading {f_name} file!')
    return s


def read_data(file_date: datetime):
    """
    Function returns collected data from teacher's timetable and list of courses on sdo.rgsu.net
    It is used for transfer data from one module to another.
    Parameter file_date is a begin of week for which we run modules.

    :param file_date: date of begin of week for which table should be imported
    :return: list
    """
    f_name = 'sdoweek_' + file_date.strftime("%d_%m_%y") + '.dat'
    try:
        with open(f_name, 'rb') as f:
            timetable = pickle.load(f)
    except Exception as e:
        print(e)
        sys.exit(Fore.RED + f'Error when reading {f_name}! You should create it first by getWeekData script.')
    print('File ' + Fore.CYAN + f_name + Fore.WHITE + ' was imported' +
          '.' * (80 - len(f_name) - 21) + Fore.GREEN + '[+]')
    return timetable
