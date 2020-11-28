#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ========================== Version 0.9 ==============================================
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
import csv
from colorama import Fore, Back
from datetime import datetime, timedelta
from infoout import mymes, getsettings
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
import sys

settings = getsettings()
login = settings[0].strip()
password = settings[1].strip()
browser = settings[4].strip()
browser_driver_path = settings[5].strip()

# List of days in the week
begin_date = datetime.now()
while begin_date.isoweekday() != 1:
    begin_date -= timedelta(1)
print('Begin of current week: ', Fore.BLACK + Back.GREEN + begin_date.strftime("%d/%m/%Y (%A)"))  # begin of week
week_dates = [begin_date + timedelta(i) for i in range(6)]

# =============================================================================
# Browser driver initialization
# =============================================================================
if browser[0] == 'F':
    from selenium.webdriver.firefox.options import Options  # for Firefox browser
elif browser[0] == 'C' or browser[0] == 'G':
    from selenium.webdriver.chrome.options import Options  # for Chrome browser

opts = Options()
# opts.add_argument("--headless")
opts.add_argument('--ignore-certificate-errors')
mymes('Driver is starting now', 0, False)
mymes("Please wait, don't close windows!", 0, False)

if browser[0] == 'F':
    # Download driver on https://github.com/mozilla/geckodriver/releases
    driver = webdriver.Firefox(options=opts, executable_path=browser_driver_path)
elif browser[0] == 'C' or browser[0] == 'G':
    # Download Chrome driver if you use Google Chrome
    # https://sites.google.com/a/chromium.org/chromedriver/home
    driver = webdriver.Chrome(chrome_options=opts, executable_path=browser_driver_path)
else:
    sys.exit('Error! Unknown name of browser. Please check requirements ans file settings.txt')

# driver = webdriver.Safari(executable_path = r'/usr/bin/safaridriver') # for MacOS

wait = WebDriverWait(driver, 20)
mymes('Headless Mode is initialized', 0)

# =============================================================================
# Login on sdo.rgsu.net
# =============================================================================
driver.get('https://sdo.rgsu.net/')
get_link = wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'login')))
get_link.click()
mymes('Opening login form', 1, False)
mymes('Entering login and password', 1, False)
driver.find_element_by_id('login').send_keys(login)
driver.find_element_by_id('password').send_keys(password)
# Submit authorization:
get_link = wait.until(ec.element_to_be_clickable((By.ID, 'submit')))
get_link.click()
# Tutor mode ON:
get_link = wait.until(ec.element_to_be_clickable((By.XPATH, '//div[@class="hm-roleswitcher"]/div[2]')))
get_link.click()

driver.maximize_window()

# =============================================================================
# Go to timetable for the next week and parse it:
# =============================================================================
get_link = wait.until(ec.element_to_be_clickable((By.XPATH, '//div[@class="wrapper"]/ul/li[7]/a')))
get_link.click()
mymes('Timetable is opening', 1)
pairs = wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, "tt-row")))
timetable = []  # array of data
for pair in pairs:
    # Read lines, parse discipline, time, date and type
    pair_cells = pair.find_elements_by_tag_name('td')
    cell3 = pair_cells[2].text  # discipline and dates in a single cell
    discipline = re.sub(r'\s?\d{2}.\d{2}.(\d{2}|\d{4});?', '', cell3).strip()
    cell_date = [date for date in week_dates if date.strftime("%d.%m.%y") in cell3][0]
    cell_date = cell_date.replace(hour=int(pair_cells[0].text.strip()[:2]),
                                  minute=int(pair_cells[0].text.strip()[3:5]), second=0, microsecond=0)
    # Append collected data to the end of list report_data:
    timetable.append({'time': cell_date, 'group': pair_cells[3].text.strip(),
                      'type': pair_cells[4].text.strip(), 'discipline': discipline})

# =============================================================================
# Go to "My Courses" page - it downloads very long !!!
# =============================================================================
mymes('Script working. Please, wait', 0, False)
driver.get(driver.find_element_by_xpath('//div[@class="wrapper"]/ul/li[2]/a').get_attribute('href'))
mymes('Loading All courses page', 1)  # pause and wait until all elements located:
wait.until(ec.presence_of_element_located((By.XPATH, '//div[@id="credits"]')))
# Find group in All courses table, parse link to course and get link to forum
mymes('Page parsing', 0, False)
courses = driver.find_elements_by_class_name("lesson_table")
# finding links to forum for course
print('Progress: [' + ' ' * len(timetable) + '] 0%', end='')
progress = 0
for lesson in timetable:
    for course in courses:
        course_text = course.find_element_by_class_name("lesson_options").text
        # checking that left table pane contains our group:
        if lesson['group'] in course_text and lesson['discipline'] in course_text:
            # finding link to page of this course
            link = course.find_element_by_id("lesson_title").find_element_by_tag_name('a').get_attribute('href')
            course_id = re.search(r'\d+$', link)[0]
            lesson['forum'] = 'https://sdo.rgsu.net/forum/subject/subject/' + course_id
            # finding link to journal of our lesson_type
            for items in course.find_elements_by_class_name("hm-subject-list-item-description-lesson-title"):
                link_elem = items.find_element_by_tag_name('a')
                if lesson['type'][:6] in link_elem.text:  # if lesson types matches
                    # save link to journal of attendance:
                    lesson['journal'] = link_elem.get_attribute('href') + '/day/all'
                    break
            print('\rProgress: [' + '#' * progress + ' ' * (len(timetable) - progress) + '] ' +
                  str(int(progress / len(timetable) * 100 + 0.5)) + '%', end='')
            progress += 1
            break  # go to next group
print('\rProgress: [' + '#' * len(timetable) + '] 100%')

# Counting number of lessons with group in one day

for i in range(len(timetable)):
    if 'group_n' not in timetable[i]:
        group_n = 1
        j = i + 1
        while (j < len(timetable)) and (timetable[i]['time'].day == timetable[j]['time'].day):
            if timetable[i]['group'] == timetable[j]['group']:
                group_n += 1
            j += 1
        j = i
        while (j < len(timetable)) and (timetable[i]['time'].day == timetable[j]['time'].day):
            if timetable[i]['group'] == timetable[j]['group']:
                timetable[j]['group_n'] = group_n
            j += 1

fieldnames = ['time', 'group', 'group_n', 'type', 'discipline', 'forum', 'journal']
f_name = 'sdoweek_' + begin_date.strftime("%d_%m_%y") + '.csv'
with open(f_name, 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writerows(timetable)

print(Fore.GREEN + "All work is done! See program report in csv file")
# input('press enter...')
driver.quit()
print("Driver Turned Off")
