#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ========================== Version 0.9 ==============================================
# CreateForumTopics  - Generate topics on sdo.rgsu.net for checking students on lessons
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
# import csv
import re
import sys
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from infoout import mymes

try:
    with open('settings.txt') as f:
        settings = f.readlines()
except(IOError, OSError) as e:
    print(e)
    print()
    sys.exit('Error when reading sdo.auth file!!!')
login = settings[0].strip()
password = settings[1].strip()
browser = settings[4].strip()
browser_driver_path = settings[5].strip()

# List of days in the week
begin_date = datetime.now()
while begin_date.isoweekday() != 1:
    begin_date -= timedelta(1)
print('Begin of current week: ', begin_date.strftime("%d/%m/%Y (%A)"))  # begin of week
week_dates = [begin_date + timedelta(i) for i in range(6)]

# =============================================================================
# Browser driver initialization
# =============================================================================
if browser[0] == 'F':
    from selenium.webdriver.firefox.options import Options  # for Firefox browser
elif browser[0] == 'C' or browser[0] == 'G':
    from selenium.webdriver.chrome.options import Options  # for Chrome browser

opts = Options()
opts.add_argument("--headless")
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
get_link = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'login')))
get_link.click()
mymes('Opening login form', 1, False)
mymes('Entering login and password', 1, False)
driver.find_element_by_id('login').send_keys(login)
driver.find_element_by_id('password').send_keys(password)
# Submit authorization:
get_link = wait.until(EC.element_to_be_clickable((By.ID, 'submit')))
get_link.click()
# Tutor mode ON:
get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="hm-roleswitcher"]/div[2]')))
get_link.click()

driver.maximize_window()

# =============================================================================
# Go to timetable for the next week and parse it:
# =============================================================================
get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="wrapper"]/ul/li[7]/a')))
get_link.click()
mymes('Timetable is opening', 1)
pairs = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "tt-row")))
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
wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="credits"]')))
# Find group in All courses table, parse link to course and get link to forum
mymes('Page parsing', 0, False)
courses = driver.find_elements_by_class_name("lesson_table")
# finding links to forum for course
print('Progress: [' + ' ' * len(timetable) + ']', end='')
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
                    lesson['journal'] = link_elem.get_attribute('href')
                    break
            print('\rProgress: [' + '#' * progress + ' ' * (len(timetable) - progress) + '] ' +
                  str(int(progress / len(timetable) * 100 + 0.5)) + '%', end='')
            progress += 1
            break  # go to next group
print('\rProgress: [' + '#' * len(timetable) + '] 100%')

# =============================================================================
# Create forum topics for all groups in timetable
# =============================================================================
k = 0
mymes("Let's make forum topics!", 0, False)
for lesson in timetable[::-1]:  # reverse order for chronological order
    driver.get(lesson['forum'])
    get_element = driver.find_element_by_xpath('//a[text()="Создать тему"]')
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', get_element)
    mymes('Adding forum topic for group ' + lesson['group'] + ' (' + lesson['time'].strftime("%H:%M") + ')', 2, False)
    get_element.click()
    get_element = driver.find_element_by_xpath('//div[@class="topic-input"]/input')
    # Отметка посещения [ГРУППА]: [ДАТА], время занятия [НАЧАЛО]-[КОНЕЦ] ([Лабораторная работа])
    get_element.send_keys('Отметка посещения ' + lesson['group'] + ': ' + lesson['time'].strftime("%d.%m.%Y") + ', ' +
                          'время занятия ' + lesson['time'].strftime("%H:%M") + '-' +
                          (lesson['time'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") +
                          ' (' + lesson['type'] + ')')
    driver.find_element_by_xpath('//a[@title="Редактировать HTML код"]').click()
    frame_id = driver.find_element_by_xpath('//iframe[starts-with(@id, "mce_")]').get_attribute('id')
    driver.switch_to.frame(frame_id)
    topic_text = '<p><span style="font-size: large;">Уважаемые студенты, данная тема предназначена только ' + \
                 'для отметки посещения пары с' + lesson['time'].strftime("%H:%M") + ' по ' + \
                 (lesson['time'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") + '!</span></p>' + \
                 '<p>Отметка производится <strong>строго</strong> во время занятия ' + \
                 '(<strong>автоматически проверяется дата и время создания сообщения</strong>). ' + \
                 '<strong>Сообщения об отметке НЕ во время занятия НЕ учитываются</strong>. ' + \
                 'Просьба написать в данной теме <strong>только одно</strong> сообщение и <strong>только, ' + \
                 'если вы присутствуете на занятии</strong> (преподаватель производит сверку ваших отметок ' + \
                 'со списком подключенных к трансляции).</p><p><strong>Создайте сообщение </strong></p>' + \
                 '<ul><li><strong>В заголовке:</strong> присутствовал(а)</li>' + \
                 '<li><strong>В сообщении:</strong> присутствовал(а)</li></ul>'
    mymes('Filling form', 1)
    driver.find_element_by_id('htmlSource').send_keys(topic_text)
    driver.find_element_by_id('insert').click()
    driver.switch_to.default_content()
    get_element = driver.find_element_by_id('submit')
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', get_element)
    mymes('Loading', 1, False)
    get_element.click()
    k += 1
    mymes('Saving topic ' + str(k) + ' of ' + str(len(timetable)) + ' (' +
          str(int(k / len(timetable) * 100 + 0.5)) + '%)', 1)

'''
fieldnames = ['time', 'group', 'type', 'discipline', 'forum', 'journal']
f_name = 'forum_links_week_' + begin_date.strftime("%d.%m.%Y") + '.csv'
with open(f_name, 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writerows(timetable)
'''

'''print('This week you have next lessons:')
for lesson in timetable:
    print(lesson['group'], lesson['forum'])
'''

print("All work is done! See program report in report.txt")
# input('press enter...')
driver.quit()
print("Driver Turned Off")
