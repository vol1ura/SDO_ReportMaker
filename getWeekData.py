#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ==================== Version 3.34 ===========================================
# ReportMaker - make teacher's report on SDO.RSSU.NET.
# 2020-2021 Yuriy Volodin, volodinjuv@rgsu.net
# =============================================================================
from colorama import Fore, Back
from datetime import datetime, timedelta
import pickle
import re
from lxml.html import fromstring, parse
from sdodriver.infoout import get_settings
from sdodriver.sdo_requests import PortalRGSU
import sys


SETTINGS = get_settings('settings.txt')
sdo = PortalRGSU(SETTINGS[0].strip(), SETTINGS[1].strip())

begin_date = datetime.now()
if len(sys.argv) > 1 and sys.argv[1] == 'n':  # if parameter n in command line
    begin_date += timedelta(7)
    timetable_link = 'https://sdo.rgsu.net/timetable/teacher/index/week/next'
else:
    timetable_link = 'https://sdo.rgsu.net/timetable/teacher'

# List of days in the week
while begin_date.isoweekday() != 1:
    begin_date -= timedelta(1)
print('Begin of the week: ', Fore.BLACK + Back.GREEN + begin_date.strftime("%d/%m/%Y (%A)"))  # begin of week
WEEKDAYS = {'Понедельник': 0, 'Вторник': 1, 'Среда': 2, 'Четверг': 3, 'Пятница': 4, 'Суббота': 5}

# =============================================================================
# Go to the timetable and parse it:
# =============================================================================
result = sdo.sdo.get(timetable_link, stream=True)
result.raw.decode_content = True
tree = parse(result.raw)
rows = tree.xpath('//tr[@class="tt-row"]')
timetable = []  # array of data
for row in rows:
    # Read lines, parse discipline, time, date and type
    cells = row.xpath('.//td/text()')
    # Lesson is online if there is no cabinet number:
    lesson_online = True if not cells[1].strip() else False
    discipline = re.sub(r'\s?\d{2}.\d{2}.(\d{2}|\d{4});?', '', cells[2]).strip()
    cell_date = begin_date + timedelta(WEEKDAYS[cells[6].strip()])
    cell_date = cell_date.replace(hour=int(cells[0].strip()[:2]),
                                  minute=int(cells[0].strip()[3:5]), second=0, microsecond=0)
    # counting lesson number for each day int timetable:
    if (len(timetable) == 0) or (timetable[-1]['time'].day != cell_date.day):
        pair_n = 1  # reset counter to 1 every new day
    else:
        if (timetable[-1]['time'].hour == cell_date.hour) and (timetable[-1]['time'].minute == cell_date.minute):
            pair_n = timetable[-1]['pair']  # increase pair counter - class number on that day
        else:
            pair_n = timetable[-1]['pair'] + 1
    # Append collected data to the end of list report_data:
    timetable.append({'time': cell_date, 'pair': pair_n, 'group': cells[3].strip(),
                      'type': cells[4].strip(), 'discipline': discipline, 'online': lesson_online})

# =============================================================================
# Go to "My Courses" page - it downloads very long !!!
# =============================================================================
print('Downloading My courses page. Please, wait...')
result = sdo.sdo.get(tree.xpath('//div[@class="wrapper"]/ul/li[2]/a/@href')[0])
tree = fromstring(result.text)
courses = tree.xpath('//*[@class="lesson_table"]')

for lesson in list(timetable):
    for course in courses:
        course_text = course.xpath('.//*[@class="lesson_options"]')[0].text_content()
        # checking that left table pane contains our group:
        if (lesson['group'] in course_text) and (lesson['discipline'] in course_text):
            # search link to page of this course
            link = course.xpath('.//div[@id="lesson_title"]/a/@href')[0]
            lesson['subject_id'] = re.search(r'\d+$', link)[0]
            # search link to journal of our lesson_type
            matches = re.finditer(r'{"CID":' + lesson['subject_id'] + r',.*? - (.*?)(?:"|\().*?lesson_id\\/(\d+)',
                                  result.text, re.MULTILINE)
            for match in matches:
                if lesson['type'][:6] in match.group(1).encode().decode('unicode-escape'):
                    lesson['lesson_id'] = match.group(2)
                    break
            break
    else:  # in case of error of sdo - group is missing in list My courses - remove this group from the list
        print(Fore.RED + '\rWarning! Group ' + lesson['group'] + ' is missing in your list "My courses".\n' +
              Fore.RESET + 'You need to address to technical support. Restart program after solving this problem. ' +
              'Now this group will be removed from data file and process will continue.')
        timetable.remove(lesson)

f_name = f'sdoweek_{begin_date.strftime("%d_%m_%y")}.dat'
with open(f_name, 'wb') as f:
    pickle.dump(timetable, f)

print(Fore.GREEN + 'All work is done! Collected data was written in ' + Fore.CYAN + f_name + Fore.GREEN + ' file.')
# input('press enter...')
