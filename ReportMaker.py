#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ==================== Version 3.34 ===========================================
# ReportMaker - make teacher's report on SDO.RSSU.NET.
# 2020-2021 Yuriy Volodin, volodinjuv@rgsu.net
# =============================================================================
from colorama import Back
from datetime import timedelta
from lxml.html import parse
import os
import re
from sdodriver import sdodriver as sdo
from sdodriver.infoout import *
from sdodriver.sdo_requests import PortalRGSU, get_table_id
from sdodriver.webdav import Cloud
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
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
local_paths = ''
video_count = 0
for file in files:
    if re.fullmatch(r'Video\d\.\w{2,5}', file):
        video_count += 1
        if not client.check(rem_path + '/' + file):
            local_paths += video_path + file + '\n'
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

attempt_to_upload = 0
if local_paths:
    mymes('Open web folder to start upload', 4)
    driver.start_cloud_upload(local_paths)

    while "none" not in driver.find_element_by_id('uploadprogressbar').get_attribute('style'):
        element = driver.find_element_by_id('uploadprogressbar')
        try:
            k = int(float(element.get_attribute('aria-valuenow')) * 40 / 100 + 0.5)
            attr = element.get_attribute('data-original-title')
            inf = re.sub(r'(\d+)(?:,\d)? (?:\w{2} ){2}(\d+)(?:,\d)?', r'\1/\2', attr)
        except (KeyError, TypeError):
            if attempt_to_upload < 5:
                driver.get('https://cloud.rgsu.net/apps/files/?dir=/' + '/'.join(rem_folders))
                attempt_to_upload += 1
                mymes(f'Attempt {attempt_to_upload} / 5 to upload failed. I\'ll try once more', 3, False)
                driver.start_cloud_upload(local_paths)
                continue
            driver.turnoff()
            raise SystemExit('Failed to start files upload. Please, restart the script. '
                             'If this error repeats, try to upload files manually.')
        print('\rProgress: |' + Back.BLUE + '#' * k + Back.RESET + ' ' * (40 - k) + f'| {inf:>26}', end='')
        sleep(0.8)
    print()
    client.free_space()

mymes('Start sharing files', 2, False)

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

driver.turnoff()

for les_data in report_data:
    les_data['video'] = video_links[les_data['pair'] - 1]

# =============================================================================
# Let's go to forum and gather students' posts TODO: refactor to class method
# =============================================================================
mymes('Login on [sdo.rgsu.net]', 0, False)
sdo = PortalRGSU(login, password)

mymes("Processing students' marks on the forum", 0, False)
for les_data in report_data:
    les_data['group_a'] = set()  # for adding students id that was on the lesson
    forum_content = sdo.sdo.get('https://sdo.rgsu.net/forum/subject/subject/' + les_data['subject_id'], stream=True)
    forum_content.raw.decode_content = True
    tree = parse(forum_content.raw)
    topics = tree.xpath('//*[@class="topic-title"]/a[1]/@href')
    for topic in topics:
        topic_title = topic.getparent().text_content()
        if (les_data['time'].strftime("%d.%m.%Y") in topic_title) and \
                (les_data['time'].strftime("%H:%M") in topic_title):
            topic_content = sdo.sdo.get(sdo.SDO_URL + topic, stream=True)
            topic_content.raw.decode_content = True
            tree = parse(topic_content.raw)
            comments = tree.xpath('//span[@class="topic-comment-author-and-pubdate"]')
            # Parse students
            for comment in comments:
                comment_date = datetime.fromisoformat(comment.xpath('.//time/@datetime')[0])
                if les_data['time'] <= comment_date <= les_data['time'] + timedelta(hours=1, minutes=30):
                    user_id = comment.xpath('.//a/@data-user-id')[0]
                    les_data['group_a'].add(user_id)
            break

# =============================================================================
# Let's go to attendance page of current lesson type TODO: refactor to class method
# =============================================================================
mymes('Attendance journals filling ', 0, False)
for les_data in report_data:
    # Find id of group
    journal_url = "https://sdo.rgsu.net/lesson/execute/index" \
                  f"/lesson_id/{les_data['lesson_id']}/subject_id/{les_data['subject_id']}/day/all"
    journal_content = sdo.sdo.get(journal_url, stream=True)
    journal_content.raw.decode_content = True
    tree = parse(journal_content.raw)
    group_id = tree.xpath(f'//select[@name="groupname"]/option[@title="{les_data["group"]}"]/@value')[0]
    # Parse journal of this group
    payload = {"groupname": group_id}
    journal_content = sdo.sdo_post(journal_url, payload=payload, stream=True)
    journal_content.raw.decode_content = True
    tree = parse(journal_content.raw)
    table_head = tree.xpath('//*[@id="journal"]/table/thead/tr/th/@id')
    for cell_head in table_head:
        id_th_day = cell_head[7:]
        # Checking column with this id for emptiness. Selecting cell with presence:
        is_be_yes_in_column = tree.xpath(f'//td[@class="is_be_row_{id_th_day}"]/div/p[@class="is-be-yes"]')
        if not is_be_yes_in_column:
            break
    else:
        print(Fore.RED + f"All columns are filled. Can't add attendance for {les_data['group']}. Journal was skipped!")
        continue
    check_string = ''.join(tree.xpath('//tbody/tr/td[@class="fio-cell"]/a/@href'))
    [les_data['group_a'].remove(user_id) for user_id in list(les_data['group_a']) if user_id not in check_string]
    action_url = tree.xpath('//form[@id="journal"]/@action')[0]
    j_type = tree.xpath('//input[@id="journal_type"]/@value')[0]
    sdo.set_attendance(action_url,
                       id_th_day,
                       j_type,
                       les_data['time'].strftime("%d.%m.%Y"),
                       les_data['online'],
                       les_data['group_a'])

# =============================================================================
# Making news TODO: refactor to class method
# =============================================================================
mymes('Making news', 0, False)
prev_group = ''
prev_link = ''
for les_data in report_data:
    if les_data['group'] == prev_group:
        les_data['news_link'] = prev_link
        continue
    if 'news_link' not in les_data:  # if news link is not generated yet:
        announce = f"Видеоматериалы занятия от {date.strftime('%d.%m.%Y')} с группой {les_data['group']}"
        news_text = f"<p>Занятие от {date.strftime('%d.%m.%Y')} г.:</p><ul>"
        for les_data1 in report_data:
            if les_data['group'] == les_data1['group']:
                news_text += '<li><a href="' + les_data1['video'] + '">Запись трансляции занятия</a>&nbsp;(' \
                             + les_data1['type'] + ',&nbsp;' + les_data1['time'].strftime("%H:%M") + ' - ' \
                             + (les_data1['time'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") + ')'
        news_text += '</ul>'

        les_data['news_link'] = sdo.make_news(announce, news_text, les_data['subject_id'])

        prev_group = les_data['group']
        prev_link = les_data['news_link']


# =============================================================================
save_report(report_data, 'report.txt')  # TODO: refactor to class method
# =============================================================================
# Open timetable page to write report  # TODO: refactor to class method
# =============================================================================
mymes('Report making', 0, False)
report_data = get_table_id(sdo, report_data)

for les_data in report_data:
    res = sdo.make_report(les_data['timetable_id'], len(les_data['group_a']),
                          les_data['video'], les_data['news_link'])
    if not res:
        print(Fore.RED + "Report record failed.",
              les_data['time'].strftime('%H:%M'), les_data['discipline'], les_data['group'])

print(Fore.GREEN + 'All work is done! See program report in ' + Fore.CYAN + 'report.txt')
# input('press enter...')
