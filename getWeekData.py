#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ========================== Version 3.3 ==============================================
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
from infoout import mymes, get_settings
import pickle
import re
import sdodriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
import sys

login, password, _, _, browser, browser_driver_path = map(str.strip, get_settings('settings.txt'))

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
week_dates = [begin_date + timedelta(i) for i in range(6)]

# Browser driver initialization
mymes("Driver is starting now. Please wait, don't close windows!", 0, False)
driver = sdodriver.Driver(browser, browser_driver_path)
# Login on sdo.rgsu.net
mymes('Login on [sdo.rgsu.net]', 0, False)
driver.open_sdo(login, password)

# =============================================================================
# Go to timetable for the next week and parse it:
# =============================================================================
driver.wait.until(ec.presence_of_element_located((By.XPATH, '//div[@class="wrapper"]')))
driver.get(timetable_link)
mymes('Timetable is opening', 1)
pairs = driver.wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, "tt-row")))
timetable = []  # array of data
for row, pair in enumerate(pairs):
    # Read lines, parse discipline, time, date and type
    pair_cells = pair.find_elements_by_tag_name('td')
    cell3 = pair_cells[2].text  # discipline and dates in a single cell
    discipline = re.sub(r'\s?\d{2}.\d{2}.(\d{2}|\d{4});?', '', cell3).strip()
    cell_date = [date for date in week_dates if date.strftime("%d.%m.%y") in cell3][0]
    cell_date = cell_date.replace(hour=int(pair_cells[0].text.strip()[:2]),
                                  minute=int(pair_cells[0].text.strip()[3:5]), second=0, microsecond=0)
    # counting lesson number for each day int timetable:
    if (len(timetable) == 0) or (timetable[-1]['time'].day != cell_date.day):
        pair_n = 1  # reset counter to 1 every new day
    else:
        if (timetable[-1]['time'].hour == cell_date.hour) and (timetable[-1]['time'].minute == cell_date.minute):
            pair_n = timetable[-1]['pair']  # increase pair counter - class number on that day
        else:
            pair_n = timetable[-1]['pair'] + 1
    # Append collected data to the end of list report_data:
    timetable.append({'row': row, 'time': cell_date, 'pair': pair_n, 'group': pair_cells[3].text.strip(),
                      'type': pair_cells[4].text.strip(), 'discipline': discipline})

# =============================================================================
# Go to "My Courses" page - it downloads very long !!!
# =============================================================================
mymes('Script working. Please, wait', 0, False)
driver.get(driver.find_element_by_xpath('//div[@class="wrapper"]/ul/li[2]/a').get_attribute('href'))
mymes('Loading All courses page', 1)  # pause and wait until all elements located:
driver.wait.until(ec.presence_of_element_located((By.XPATH, '//div[@id="credits"]')))
# Find group in All courses table, parse link to course and get link to forum
mymes('Page parsing', 0, False)
courses = driver.find_elements_by_class_name("lesson_table")
# finding links to forum for course


def parse_courses(les):
    global progress, courses
    for course in courses:
        course_text = course.find_element_by_class_name("lesson_options").text
        # checking that left table pane contains our group:
        if (les['group'] in course_text) and (les['discipline'] in course_text):
            # finding link to page of this course
            link = course.find_element_by_xpath('.//div[@id="lesson_title"]/a').get_attribute('href')
            course_id = re.search(r'\d+$', link)[0]
            les['forum'] = 'https://sdo.rgsu.net/forum/subject/subject/' + course_id
            les['news'] = 'https://sdo.rgsu.net/news/index/index/subject_id/' + course_id + '/subject/subject'
            # finding link to journal of our lesson_type
            menu = course.find_elements_by_xpath('.//div[@class="hm-subject-list-item-description-lesson-title"]/a')
            for link in menu:
                if les['type'][:6] in link.text:  # if lesson types matches
                    # save link to journal of attendance:
                    les['journal'] = link.get_attribute('href') + '/day/all'
                    break
            progress += 1
            s = int(50 * progress / len(timetable) + 0.5)
            print('\rProgress: |' + Back.BLUE + '#' * s + Back.WHITE +
                  ' ' * (50 - s) + Back.RESET + f'| {2 * s:>4}%', end='')
            break  # go to next group
    else:  # in case of error of sdo - group is missing in list My courses - remove this group from the list
        print(Fore.RED + '\rWarning! Group ' + les['group'] + ' is missing in your list "My courses".')
        print('You need to address to technical support. Restart program after solving this problem.')
        print('Now this group will be removed from data file and process will continue.')
        timetable.remove(les)


print('Progress: |' + Back.WHITE + ' ' * 50 + Back.RESET + '| ' + '0%'.rjust(4), end='')
progress = 0
with ThreadPoolExecutor(8) as executor:
    executor.map(parse_courses, list(timetable))
print('\rProgress: |' + Back.BLUE + '#' * 50 + Back.RESET + '| ' + Fore.GREEN + '100%')

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
driver.turnoff()
