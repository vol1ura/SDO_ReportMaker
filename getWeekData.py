#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ========================== Version 3.31 ==============================================
# getWeekData  - Generate csv file with timetable data
# Copyright (c) 2020 Yuriy Volodin volodinjuv@rgsu.net
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
from colorama import Fore, Back
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timedelta
import pickle
import re
from lxml.html import fromstring, parse
from sdodriver.infoout import get_settings
from sdodriver.sdo_requests import Session
import sys


login, password, _, _, _, _ = map(str.strip, get_settings('settings.txt'))
session = Session(login, password)

begin_date = datetime.now()
if len(sys.argv) > 1 and sys.argv[1] == 'n':  # if parameter n in command line
    begin_date += timedelta(7)
    timetable_link = 'https://sdo.rgsu.net/timetable/teacher/index/week/next'
else:
    timetable_link = 'https://sdo.rgsu.net/timetable/teacher'

# List of days in the week
while begin_date.isoweekday() != 1:
    begin_date -= timedelta(1)
print('Begin of week: ', Fore.BLACK + Back.GREEN + begin_date.strftime("%d/%m/%Y (%A)"))  # begin of week
WEEKDAYS = {'Понедельник': 0, 'Вторник': 1, 'Среда': 2, 'Четверг': 3, 'Пятница': 4, 'Суббота': 5}

# =============================================================================
# Go to timetable for the next week and parse it:
# =============================================================================
result = session.sdo.get(timetable_link, stream=True)
result.raw.decode_content = True
tree = parse(result.raw)
rows = tree.xpath('//tr[@class="tt-row"]')
timetable = []  # array of data
for i, row in enumerate(rows):
    # Read lines, parse discipline, time, date and type
    cells = row.xpath('.//td/text()')
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
    timetable.append({'row': i, 'time': cell_date, 'pair': pair_n, 'group': cells[3].strip(),
                      'type': cells[4].strip(), 'discipline': discipline})

# =============================================================================
# Go to "My Courses" page - it downloads very long !!!
# =============================================================================
print('Page parsing. Please, wait...')
result = session.sdo.get(tree.xpath('//div[@class="wrapper"]/ul/li[2]/a/@href')[0])
tree = fromstring(result.text)
courses = tree.xpath('//*[@class="lesson_table"]')


def parse_courses(les):
    """
    Find group in All courses table, parse link to course and get links to forum, to news page and to journal

    :param les: list with lesson data
    """
    global progress, courses
    for course in courses:
        course_text = course.xpath('.//*[@class="lesson_options"]')[0].text_content()
        # checking that left table pane contains our group:
        if (les['group'] in course_text) and (les['discipline'] in course_text):
            # finding link to page of this course
            link = course.xpath('.//div[@id="lesson_title"]/a/@href')[0]
            course_id = re.search(r'\d+$', link)[0]
            les['forum'] = 'https://sdo.rgsu.net/forum/subject/subject/' + course_id
            les['news'] = f'https://sdo.rgsu.net/news/index/index/subject_id/{course_id}/subject/subject'
            # finding link to journal of our lesson_type
            matches = re.finditer(r'{"CID":' + course_id + r',.*? - (.*?)(?:"|\().*?lesson_id\\/(\d+)',
                                  result.text, re.MULTILINE)
            for match in matches:
                if les['type'][:6] in match.group(1).encode().decode('unicode-escape'):
                    les['journal'] = f'https://sdo.rgsu.net/lesson/execute/index/lesson_id/{match.group(2)}' + \
                                     f'/subject_id/{course_id}/day/all'
                    break
            progress += 1
            s = int(50 * progress / len(timetable) + 0.5)
            print('\rProgress: |' + Back.BLUE + '#' * s + Back.WHITE +
                  ' ' * (50 - s) + Back.RESET + f'| {2 * s:>4}%', end='')
            break
    else:  # in case of error of sdo - group is missing in list My courses - remove this group from the list
        print(Fore.RED + '\rWarning! Group ' + les['group'] + ' is missing in your list "My courses".\n' +
              Fore.RESET + 'You need to address to technical support. Restart program after solving this problem. ' +
              'Now this group will be removed from data file and process will continue.')
        timetable.remove(les)


print('Progress: |' + Back.WHITE + ' ' * 50 + Back.RESET + '|   0%', end='')
progress = 0
with ThreadPoolExecutor(8) as executor:
    executor.map(parse_courses, list(timetable))
print('\rProgress: |' + Back.BLUE + '#' * 50 + Back.RESET + '| ' + Fore.GREEN + '100% ')

# Counting number of lessons with group in one day
for i in range(len(timetable)):
    if 'group_n' not in timetable[i]:
        group_n = 1
        j = i + 1
        while (j < len(timetable)) and (timetable[i]['time'].day == timetable[j]['time'].day):
            if timetable[i]['group'] == timetable[j]['group']:
                group_n += 1  # counting through each day
            j += 1
        j = i
        while (j < len(timetable)) and (timetable[i]['time'].day == timetable[j]['time'].day):
            if timetable[i]['group'] == timetable[j]['group']:
                timetable[j]['group_n'] = group_n  # then write the counter to every group record
            j += 1

f_name = f'sdoweek_{begin_date.strftime("%d_%m_%y")}.dat'
with open(f_name, 'wb') as f:
    pickle.dump(timetable, f)

print(Fore.GREEN + 'All work is done! Collected data was written in ' + Fore.CYAN + f_name + Fore.GREEN + ' file.')
# input('press enter...')
