#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ==================== Version 3.32 =================================
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
from colorama import Back
from datetime import timedelta
import os
import re
from sdodriver import sdodriver as sdo
from sdodriver.infoout import *
from sdodriver.webdav import Cloud
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
import sys
from time import sleep


login, password, token, video_path, browser, browser_driver_path = map(str.strip, get_settings('settings.txt'))

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

report_data = read_data(date_wd)
for les_data in list(report_data):
    if les_data['time'].day != date.day:
        report_data.remove(les_data)

report_data.sort(key=lambda les: les['group'])  # sorting by group to minimize page reloads

# =============================================================================
# Unloading video files on cloud.sdo.net
# =============================================================================
client = Cloud(login, password, token)
mymes('WebDAV protocol is initialized', 0)

rem_folders = ['Запись занятий', date.strftime("%Y") + '_год', date.strftime("%m") + '_месяц', date.strftime('%m_%d')]

rem_path = ''
for folder in rem_folders:
    rem_path += folder + '/'
    client.check_path(rem_path)

client.free_space()

files = os.listdir(video_path)
local_paths = ""
video_count = 0
for file in files:
    if re.fullmatch(r'Video\d\.\w{2,5}', file):
        video_count += 1
        if not client.check(rem_path + '/' + file):
            local_paths += video_path + file + "\n"
            print('File [' + Fore.CYAN + file + Fore.RESET + '] will be uploaded.')
        else:
            print('File [' + Fore.CYAN + file + Fore.RESET + '] has already been uploaded and will be skipped.')

pair_count = 0
for les_data in report_data:
    if les_data['pair'] > pair_count:
        pair_count = les_data['pair']

if pair_count != video_count:
    sys.exit(Fore.RED + f'Error! Number of video files ({video_count}) ' +
             f'and number of lessons in this day ({pair_count}) is not match.')

# =============================================================================
# Generating links for files on cloud.sdo.net through web interface
# =============================================================================
# Browser driver initialization
mymes("Driver is starting now. Please wait, don't close windows!", 0, False)
driver = sdo.Driver(browser, browser_driver_path)
mymes('Open [cloud.rgsu.net] for uploading and sharing files.', 0, False)
driver.open_cloud(login, password)
mymes('Authorization', 3)

driver.wait.until(ec.presence_of_element_located((By.XPATH, '//div[@id="controls"]')))
driver.get('https://cloud.rgsu.net/apps/files/?dir=/' + '/'.join(rem_folders))

if len(local_paths) > 0:
    mymes('Open web folder to start upload', 3, False)
    driver.wait.until(ec.presence_of_element_located((By.XPATH, '//div[@id="controls"]')))

    element = driver.find_element_by_xpath('//input[@type="file"]')
    element.send_keys(local_paths.strip())

    mymes('Task for upload was created', 2)
    while "none" not in driver.find_element_by_id('uploadprogressbar').get_attribute('style'):
        element = driver.find_element_by_id('uploadprogressbar')
        try:
            k = int(float(element.get_attribute('aria-valuenow')) * 40 / 100 + 0.5)
            attr = element.get_attribute('data-original-title')
            inf = re.sub(r'(\d+)(?:,\d)? (?:\w{2} ){2}(\d+)(?:,\d)?', r'\1/\2', attr)
        except KeyError:
            k = 40
            inf = 'done...'
        print('\rProgress: |' + Back.BLUE + '#' * k + Back.RESET + ' ' * (40 - k) + f'| {inf:>26}', end='')
        sleep(0.8)
    print('')
    client.free_space()
    mymes('Start sharing files', 1, False)

video_links = []
fileList = driver.wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="fileList"]')))
share_buttons = fileList.find_elements_by_xpath('.//a[@data-action="Share"]/span[1]')
for b in share_buttons:
    b.click()
    mymes('Sharing file', 2.5)
    try:
        driver.wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="sharing"]/ul[1]/li/button'))).click()
    except TimeoutException:
        print(Fore.YELLOW + 'It seems the file is already shared. I will try to get the link.')
    # One click somewhere to close menu:
    driver.find_element_by_xpath('//*[@id="filestable"]/tfoot/tr/td[2]/span/span[3]').click()
    link_button = driver.wait.until(ec.element_to_be_clickable((By.XPATH, '//ul[@class="sharing-link-list"]/li/a')))
    video_links.append(link_button.get_attribute('href').strip())  # add link

for les_data in report_data:
    les_data['video'] = video_links[les_data['pair'] - 1]

# =============================================================================
# Let's go to forum and gather students' posts
# =============================================================================
mymes('Login on [sdo.rgsu.net]', 0, False)
driver.open_sdo(login, password)

prev_group = ''
for les_data in report_data:
    if les_data['group'] != prev_group:
        prev_group = les_data['group']
        # Go to forum. Take lesson from timetable
        driver.get(les_data['forum'])
        mymes('Checking attendance of students', 1, False)
    les_data['group_a'] = set()  # for adding students id that was on the lesson
    # Parse students
    topics = driver.find_elements_by_xpath('//li[@class="topic topic-text-loaded"]')
    for topic in topics:
        topic_title = topic.find_element_by_class_name('topic-title').text
        if (les_data['time'].strftime("%d.%m.%Y") in topic_title) and \
                (les_data['time'].strftime("%H:%M") in topic_title):
            element = topic.find_element_by_class_name('topic-expand-comments')
            driver.scroll_page(element, 1)
            element.click()  # expand all comments
            mymes('Opening and gathering messages', 1, False)
            comments = topic.find_elements_by_class_name('topic-comment-author-and-pubdate')
            for comment in comments:
                comment_date = comment.find_element_by_tag_name('time').get_attribute('datetime')
                comment_date = datetime.fromisoformat(comment_date)
                if les_data['time'] <= comment_date <= les_data['time'] + timedelta(hours=1, minutes=30):
                    comment_user_url = comment.find_element_by_xpath('.//a').get_attribute('href')
                    les_data['group_a'].add(re.search(r'(?<=user_id/)\d+', comment_user_url)[0])

# =============================================================================
# Let's go to attendance page of current lesson type
# =============================================================================
prev_group = ''
for les_data in report_data:
    if les_data['group'] != prev_group:
        driver.get(les_data['journal'])
        prev_group = les_data['group']
        mymes('Loading attendance journal', 1)
        # ######### Preparing journal for parsing and filling up #######################################################
        # Open drop-down menu
        try:
            select_group = driver.wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="groupname"]')))
        except TimeoutException:
            print(Fore.RED + f"Warning! Can't open attendance journal for {les_data['group']}. It will be skipped.")
            prev_group = ''  # to re-load page and try next time if this group meet on next step
            continue
        # cycle through elements in drop-down list to find our group
        element = select_group.find_elements_by_tag_name("option")  # groups in drop-down menu
        if len(element) > 2:  # if only one group in journal drop-down menu then this step will be skipped:
            for list_item in element:  # select group in menu:
                if les_data['group'] in list_item.text:
                    select_group.click()  # click dropdown list
                    list_item.click()  # click group
                    break
            driver.find_element_by_xpath('//*[@id="marksheet-form-filters"]/div/div[2]/button').click()  # filter button
            sleep(1.5)
    mymes('Filling attendance journal for ' + les_data['group'], 0, False)
    element = driver.wait.until(ec.element_to_be_clickable((By.XPATH, '//*[@id="main"]/div[3]')))
    driver.scroll_page(element, 1)
    element.click()  # close menu panel
    # ######## End of preparation page #############################################################################
    # Get head of journal table:
    table_head = driver.find_element_by_xpath('//*[@id="journal"]/table/thead/tr')
    for cell_head in table_head.find_elements_by_tag_name('th')[1:-2]:
        id_th_day = cell_head.get_attribute('id')[7:]
        # Checking column with this id for emptiness. Selecting cell with presence:
        id_column = driver.find_elements_by_xpath(f'//td[@class="is_be_row_{id_th_day}"]/div/p')
        for id_cell in id_column:
            if id_cell.text == 'Был':
                break
        else:  # If all column is empty then change date of column and fill it by clicking checkboxes:
            element = driver.find_element_by_xpath(f'//a[contains(@onclick, "{id_th_day}")]')
            driver.scroll_page(element, 1)
            element.click()  # select edit mode of date field
            element = driver.find_element_by_xpath(f'//input[contains(@id, "{id_th_day}")]')
            element.send_keys(Keys.BACKSPACE * 10)
            element.send_keys(les_data['time'].strftime("%d.%m.%Y"))  # Set date for column
            # Check students in journal and count them
            for user_id in list(les_data['group_a']):
                try:
                    element = driver.find_element_by_xpath(f'//input[@id="isBe_user_{user_id}_{id_th_day}"]')
                except(TimeoutException, NoSuchElementException):
                    les_data['group_a'].remove(user_id)
                    continue
                driver.scroll_page(element, 1)
                element.click()
            break  # Exit cycle by head of table and go to next les_data
    element = driver.find_element_by_xpath('//*[@id="main"]/div[3]')
    driver.scroll_page(element, 1)
    element.click()  # open menu panel
    element = driver.find_element_by_xpath('//input[@value="Сохранить"]')
    driver.scroll_page(element, 1)
    element.click()
    driver.find_elements_by_xpath('//div/button[1]/span')[0].click()  # /html/body/div[2]/div[3]/div/button[1]/span
    mymes('Journal is completed', 2)

# =============================================================================
# Making news  TODO: rewrite this block using requests
# =============================================================================
prev_group = ''
prev_link = ''
for les_data in report_data:
    if les_data['group'] == prev_group:
        les_data['news_link'] = prev_link
        continue
    if 'news_link' not in les_data:  # if news link is not generated yet:
        driver.get(les_data['news'])
        mymes('Loading news page', 2)
        driver.find_element_by_partial_link_text('Создать новость').click()
        mymes('Loading news form', 2)
        driver.find_element_by_tag_name("html").send_keys(Keys.PAGE_DOWN)
        announce = f"Видеоматериалы занятия от {date.strftime('%d.%m.%Y')} с группой {les_data['group']}"
        news_text = f"<p>Занятие от {date.strftime('%d.%m.%Y')} г.:</p><ul>"
        for les_data1 in report_data:
            if les_data['group'] == les_data1['group']:
                news_text += '<li><a href="' + les_data1['video'] + '">Запись трансляции занятия</a>&nbsp;(' \
                             + les_data1['type'] + ',&nbsp;' + les_data1['time'].strftime("%H:%M") + ' - ' \
                             + (les_data1['time'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") + ')'
        news_text += '</ul>'
        get_link = driver.wait.until(ec.presence_of_element_located((By.ID, 'announce')))
        get_link.send_keys(announce)
        get_link = driver.wait.until(ec.presence_of_element_located((By.ID, 'message_code')))
        get_link.click()
        mymes('Loading edit form', 1)
        driver.switch_to.frame("mce_13_ifr")
        driver.find_element_by_xpath('//*[@id="htmlSource"]').send_keys(news_text)
        driver.find_element_by_id('insert').click()
        driver.switch_to.default_content()
        driver.find_element_by_id('submit').click()
        get_link = driver.wait.until(
            ec.presence_of_element_located((By.XPATH, '//a[contains(text(), "Видеоматериалы занятия от")]')))
        les_data['news_link'] = get_link.get_attribute('href')
        prev_group = les_data['group']
        prev_link = les_data['news_link']


# =============================================================================
with open('report.txt', 'w') as f:
    f.write(' ' * 20 + 'This day you have next lessons\n')
    f.write('N  time \tlesson_type \tgroup\t students\tCloud link\tNews link\n')
    f.write('-' * 80 + '\n')
    for les_data in report_data:
        f.write(f"{les_data['pair']}  {les_data['time'].strftime('%H:%M')}\t{les_data['type']} " +
                f"{les_data['group']}\t{len(les_data['group_a'])}\n{les_data['video']}\n{les_data['news_link']}\n\n")
# =============================================================================
# Open timetable page to write report  TODO: rewrite this block using requests
# =============================================================================
driver.get('https://sdo.rgsu.net/timetable/teacher')
mymes('Report making', 2, False)
for les_data in report_data:
    pairs = driver.wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'tt-row')))
    report_button = pairs[les_data['row']].find_element_by_tag_name('button')
    driver.scroll_page(report_button, 1)
    report_button.click()
    driver.find_element_by_name("users").send_keys(Keys.BACKSPACE + f"{len(les_data['group_a'])}")
    driver.find_element_by_name("file_path").send_keys(Keys.BACKSPACE + les_data['video'])
    driver.find_element_by_name("subject_path").send_keys(Keys.BACKSPACE + les_data['news_link'])
    driver.find_element_by_xpath('//div[@class="ui-dialog-buttonset"]/button[1]').click()
    mymes('Report for ' + les_data['group'], 2)

print(Fore.GREEN + 'All work is done! See program report in ' + Fore.CYAN + 'report.txt')
driver.turnoff()
# input('press enter...')
