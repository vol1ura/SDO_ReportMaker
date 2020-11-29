#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ==================== Version 2.0 =================================
# ReportMaker - make teacher's report on SDO.RSSU.NET.
# Copyright (c) 2020 Yuriy Volodin, volodinjuv@rgsu.net
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
import re
from datetime import datetime, timedelta

from colorama import Fore, Back

from infoout import mymes, getsettings, readfiledata
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import sys
from time import sleep
from webdav3.client import Client
# ============================================================================

settings = getsettings('settings.txt')
login = settings[0].strip()
password = settings[1].strip()
token = settings[2].strip()
video_path = settings[3].strip()
browser = settings[4].strip().upper()
browser_driver_path = settings[5].strip()

date_wd = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
if len(sys.argv) < 2:
    date = date_wd
else:
    date = datetime.strptime(sys.argv[1], '%d.%m.%' + 'y' if len(sys.argv[1]) < 9 else 'Y')
date_str = date.strftime("%d.%m.%y")
print('Date of report:' + Fore.BLACK + Back.GREEN + date_str)

while date_wd.isoweekday() != 1:
    date_wd -= timedelta(1)
if date < date_wd or date - date_wd > timedelta(6):
    sys.exit(Fore.RED + 'Error! Cannot make a report for this date. Check date in settings.txt')

report_data = readfiledata(date_wd)
for les_data in list(report_data):
    if les_data['time'].day != date.day:
        report_data.remove(les_data)


def scroll_page(web_element, t=2):
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', web_element)
    sleep(t)


def free_space():
    fs = float(client.free())
    for i in range(3):
        fs /= 1024
    color = Fore.RED if fs < 10 else Fore.GREEN
    print('Free space in your cloud [cloud.rgsu.net]:' + color + '{0:.1f}'.format(fs) + Fore.WHITE + ' Gb')


def check_path(p_dir: str):
    if not client.check(p_dir):
        client.mkdir(p_dir)
        print('Directory [{}] created.'.format(p_dir))


# =============================================================================
# Unloading video files on cloud.sdo.net
# =============================================================================
opts = {  # TODO сделать отдельный модуль загрузки и получения ссылкок - через селениум!!!
    'webdav_hostname': token,
    'webdav_login': login,
    'webdav_password': password,
}
client = Client(opts)  # using webdav protocol for files uploading

mymes('WebDAV protocol initialized', 0)

rem_folders = ['Запись занятий', date.strftime("%Y") + '_год', date.strftime("%m") + '_месяц', date.strftime('%m_%d')]

rem_path = ''
for folder in rem_folders:
    rem_path += folder + '/'
    check_path(rem_path)

free_space()

files = os.listdir(video_path)
mymes('Uploading videos. Please wait!', 0, False)
for file in files:
    if re.fullmatch(r'Video\d\.\w{2,5}', file):
        if not client.check(rem_path + '/' + file):
            client.upload_sync(remote_path=rem_path + '/' + file, local_path=os.path.join(video_path, file))
            mymes('File [' + file + '] is unloaded', 0)
        else:
            print('File [' + file + '] has already been uploaded and will be skipped.')

mymes('Uploading of all files on rgsu.cloud.net is complete', 0)
free_space()

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
    sys.exit('\033[31mError! Unknown name of browser. Please check requirements ans file settings.txt\033[0m')

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
# Let's go to forum and count students
# =============================================================================
for les_data in report_data:
    # Go to forum. Take lesson from timetable
    driver.get(les_data['forum'])
    attendance_set = set([])
    # Parse students
    mymes('Checking attendance of students', 1, False)
    topics = driver.find_elements_by_xpath('//li[@class="topic topic-text-loaded"]')
    for topic in topics:
        topic_title = topic.find_element_by_class_name('topic-title').text
        if (les_data['date'].strftime("%d.%m.%Y") in topic_title) and (les_data['date'].strftime("%H:%M") in topic_title):
            element = topic.find_element_by_class_name('topic-expand-comments')
            scroll_page(element)
            element.click()  # expand all comments
            mymes('Opening and gathering messages', 1, False)
            comments = topic.find_elements_by_class_name('topic-comment-author-and-pubdate')
            for comment in comments:
                comment_date = comment.find_element_by_tag_name('time').get_attribute('datetime')
                comment_date = datetime.fromisoformat(comment_date)
                comment_name = re.search(r'[a-zа-яё\-\s]+', comment.text, re.I)[0]
                if les_data['date'] <= comment_date <= les_data['date'] + timedelta(hours=1, minutes=30):
                    attendance_set.add(comment_name)
    print(attendance_set)
    # =============================================================================
    # Let's go to attendance page of current lesson type
    # =============================================================================
    attendance_count = 0  # attendance counter
    driver.get(les_data['journal'])
    mymes('Loading journal (attendance page)', 1)
    # Preparing journal for parsing and filling up ###########################################################
    element = wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="main"]/div[3]')))
    element.click()  # close menu panel
    # Open drop-down menu
    select_group = wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="groupname"]')))
    # cycle through elements in drop-down list to find our group
    for list_item in select_group.find_elements_by_tag_name("option"):
        # if group is founded, open journal and counting attendance
        if les_data['group'] in list_item.text:
            select_group.click()  # click dropdown list
            list_item.click()  # click group
            print(list_item.text)  # Print selected group name
            break
    driver.find_element_by_xpath('//*[@id="marksheet-form-filters"]/div/div[2]/button').click()  # filter button click
    mymes('Filling attendance of students', 1, False)
    # ###########################################################################################################
    # Get head of journal table:
    table_head = wait.until(ec.presence_of_element_located((By.XPATH, '//*[@id="journal"]/table/thead/tr')))
    for cell_head in table_head.find_elements_by_tag_name('th')[1:-2]:
        id_th_day = cell_head.get_attribute('id')[7:]
        # Checking column with this id for emptiness. Selecting cell with presence:
        id_column = driver.find_elements_by_xpath('//td[@class="is_be_row_' + id_th_day + '"]/div/p')
        for id_cell in id_column:
            if id_cell.text == 'Был':
                break
        else:  # Заполняем столбец галочками о посещениях и ставим дату
            element = driver.find_element_by_xpath('//a[contains(@onclick, "' + id_th_day + '")]')
            scroll_page(element, 1)
            element.click()
            element = driver.find_element_by_xpath('//input[contains(@id, "' + id_th_day + '")]')
            element.send_keys(Keys.BACKSPACE * 10)
            element.send_keys(les_data['date'].strftime("%d.%m.%Y"))  # Set date for column
            # Check students in journal and count them
            journal_rows = driver.find_elements_by_xpath('//tr[contains(@class, "fio-cell")]')
            for journal_row in journal_rows:
                if journal_row.find_element_by_tag_name('b').text in attendance_set:
                    scroll_page(journal_row, 1)
                    attendance_count += 1
                    get_link = journal_row.find_element_by_tag_name('a').get_attribute('href')
                    id_user = re.search(r'\d+$', get_link)[0]
                    journal_row.find_element_by_id('isBe_user_' + id_user + '_' + id_th_day).click()
            break  # Exit cycle by head of table and go to next les_data
    element = driver.find_element_by_xpath('//*[@id="main"]/div[3]')
    scroll_page(element, 1)
    element.click()  # open meny panel
    element = driver.find_element_by_xpath('//input[@value="Сохранить"]')
    les_data['attendance'] = attendance_count
    scroll_page(element)
    element.click()
    driver.find_elements_by_xpath('//div/button[1]/span')[0].click()  # /html/body/div[2]/div[3]/div/button[1]/span
    mymes('Journal is comleted', 2)


for les_data in report_data:
    print(les_data)

# =============================================================================
# Generating links for files on cloud.sdo.net through web interface
# =============================================================================

mymes('Now links will be generated through web interface.', 0, False)
driver.get('https://cloud.rgsu.net/')
mymes('Entering login and password', 1)
driver.find_element_by_id('user').send_keys(login)
driver.find_element_by_id('password').send_keys(password)
driver.find_element_by_id('submit-form').click()
mymes('Authorization', 2)

driver.get('https://cloud.rgsu.net/apps/files/?dir=/' + '/'.join(rem_folders))
fileList = wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="fileList"]')))
video_links = []
share_buttons = fileList.find_elements_by_xpath('//td[2]/a/span[2]/a[1]/span[1]')
for b in share_buttons:
    b.click()
    mymes('Sharing file', 2)
    wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="sharing"]/ul[1]/li/button'))).click()
    # One click somewhere to close menu:
    driver.find_element_by_xpath('//*[@id="filestable"]/tfoot/tr/td[2]/span/span[3]').click()
    link_button = wait.until(ec.element_to_be_clickable((By.XPATH, '//ul[@class="sharing-link-list"]/li/a')))
    video_links.append(link_button.get_attribute('href').strip())  # add link

for les_data in report_data:
    les_data['video'] = video_links[les_data['pair'] - 1]

# =============================================================================
# Making news
# =============================================================================
for les_data in report_data:
    if 'news_link' not in les_data:  # если ещё не сделали новости и не записали ссылку на новость, то:
        driver.get(les_data['news'])
        mymes('Loading news page', 2)
        driver.find_element_by_partial_link_text('Создать новость').click()
        mymes('Loading news form', 2)
        driver.find_element_by_tag_name("html").send_keys(Keys.PAGE_DOWN)
        announce = 'Видеоматериалы занятия от ' + date.strftime("%d.%m.%Y") + ' с группой ' + les_data['group']
        news_text = '<p>Занятие от ' + date.strftime("%d.%m.%Y") + ' г.:</p><ul>'
        for les_data1 in report_data:
            if les_data['group'] == les_data1['group']:
                news_text += '<li><a href="' + les_data1['video'] + '">Запись трасляции занятия</a>&nbsp;(' \
                             + les_data1['type'] + ',&nbsp;' + les_data1['date'].strftime("%H:%M") + ' - ' \
                             + (les_data1['date'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") + ')'
        news_text += '</ul>'
        get_link = wait.until(ec.presence_of_element_located((By.ID, 'announce')))
        get_link.send_keys(announce)
        get_link = wait.until(ec.presence_of_element_located((By.ID, 'message_code')))
        get_link.click()
        mymes('Loading edit form', 1)
        driver.switch_to.frame("mce_13_ifr")
        driver.find_element_by_xpath('//*[@id="htmlSource"]').send_keys(news_text)
        driver.find_element_by_id('insert').click()
        driver.switch_to.default_content()
        driver.find_element_by_id('submit').click()
        mymes('Saving news', 1)  # This timeout is no needed and can be commented or deleted!
        get_link = wait.until(
            ec.presence_of_element_located((By.XPATH, '//a[contains(text(), "Видеоматериалы занятия от")]')))
        les_data['news_link'] = get_link.get_attribute('href')
        if les_data['group_n'] > 1:
            for les_data1 in report_data:
                if (les_data['group'] == les_data1['group']) and ('news_link' not in les_data):
                    les_data1['news_link'] = les_data['news_link']


for les_data in report_data:  # TODO REMOVE after testing
    print(les_data)


# =============================================================================
# Open timetable page to write report        
# =============================================================================
get_link = wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="main"]/div[1]/div/ul/li[7]/a')))
get_link.click()  # TODO сделать переход по прямой ссылке
for les_data in report_data:
    pairs = driver.find_elements_by_class_name("tt-row")
    report_button = pairs[les_data['row']].find_element_by_tag_name('button')
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', report_button)  # REFACTOR
    mymes('Adding report', 2)
    report_button.click()
    if 'attendance' not in les_data:
        print(Back.RED + 'Attention! ' + 'Attendance for ' + les_data['group'] + ' has not been calculated!')
        print(Fore.RED + 'Verify that journals are filled out correctly and make corrections manually.')
        les_data['attendance'] = 0
    driver.find_element_by_name("users").send_keys(Keys.BACKSPACE + str(les_data['attendance']))
    driver.find_element_by_name("file_path").send_keys(Keys.BACKSPACE + les_data['video'])
    driver.find_element_by_name("subject_path").send_keys(Keys.BACKSPACE + les_data['news_link'])
    driver.find_element_by_xpath('//div[@class="ui-dialog-buttonset"]/button[1]').click()


print('This day you have next lessons:')  # TODO REMOVE after testing
for les_data in report_data:
    print(les_data)


with open('report.txt', 'w') as f:
    f.write('This day you have next lessons\n\n')
    f.write('N\ttime time\tlesson_type\tgroup\t students\t Link in cloud.sdo.net\t Link in news\n\n')
    for les_data in report_data:
        f.write(les_data['pair'] + '\t' + les_data['time'].strftime("%H:%M") + '\t' + les_data['type'] + ' ' +
                les_data['group'] + '\t' + str(les_data['attendance']) + '\t' + les_data['video'] + ' ' +
                les_data['news_link'] + '\n\n')


print(Fore.GREEN + 'All work is done! See program report in report.txt')
# input('press enter...')
driver.quit()
print("Driver Turned Off")
