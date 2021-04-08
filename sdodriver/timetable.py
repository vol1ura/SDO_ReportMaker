import re
from datetime import datetime, timedelta
from pprint import pprint

from lxml.html import parse

from infoout import get_settings, read_data
from sdo_requests import PortalRGSU

TIMETABLE = 'https://sdo.rgsu.net/timetable/teacher'
TIMETABLE_N = 'https://sdo.rgsu.net/timetable/teacher/index/week/next'
WEEKDAYS = {'Понедельник': 0, 'Вторник': 1, 'Среда': 2, 'Четверг': 3, 'Пятница': 4, 'Суббота': 5}


class Timetable:
    __SETTINGS = get_settings('../settings.txt')

    def __init__(self, week=None):
        self.__sdo = PortalRGSU(Timetable.__SETTINGS[0].strip(), Timetable.__SETTINGS[1].strip())
        self.lessons = []  # array of data
        self.__begin_date = datetime.now()
        if week == 'n':  # if parameter n in command line
            self.__begin_date += timedelta(7)
        while self.__begin_date.isoweekday() != 1:
            self.__begin_date -= timedelta(1)

    def parse(self, week=None):
        timetable_link = TIMETABLE_N if week == 'n' else TIMETABLE
        result = self.__sdo.sdo.get(timetable_link, stream=True)
        result.raw.decode_content = True
        tree = parse(result.raw)
        rows = tree.xpath('//tr[@class="tt-row"]')
        for row in rows:
            # Read lines, parse discipline, time, date and type
            cells = row.xpath('.//td/text()')
            discipline = re.sub(r'\s?\d{2}.\d{2}.(\d{2}|\d{4});?', '', cells[2]).strip()
            cell_date = self.__begin_date + timedelta(WEEKDAYS[cells[6].strip()])
            cell_date = cell_date.replace(hour=int(cells[0].strip()[:2]),
                                          minute=int(cells[0].strip()[3:5]), second=0, microsecond=0)
            # counting lesson number for each day int timetable:
            if (len(self.lessons) == 0) or (self.lessons[-1]['time'].day != cell_date.day):
                pair_n = 1  # reset counter to 1 every new day
            else:
                if (self.lessons[-1]['time'].hour == cell_date.hour) and (
                        self.lessons[-1]['time'].minute == cell_date.minute):
                    pair_n = self.lessons[-1]['pair']  # increase pair counter - class number on that day
                else:
                    pair_n = self.lessons[-1]['pair'] + 1
            # Append collected data to the end of list report_data:
            self.lessons.append({'time': cell_date, 'pair': pair_n, 'group': cells[3].strip(),
                                 'type': cells[4].strip(), 'discipline': discipline})

    def load(self):
        self.lessons = read_data(self.__begin_date)


if __name__ == '__main__':
    t = Timetable()
    print(t.lessons)
    t.parse()
    pprint(t.lessons)
