#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ========================== Version 3.31 =====================================
# CreateForumTopics  - Generate topics on sdo.rgsu.net for checking students
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
# =============================================================================
from colorama import Back
from datetime import timedelta
import requests
from sdodriver.infoout import *
import sys


begin_date = datetime.now()
if len(sys.argv) > 1 and sys.argv[1] == 'n':  # if parameter n in command line
    begin_date += timedelta(7)

while begin_date.isoweekday() != 1:
    begin_date -= timedelta(1)
print('Begin of week: ', Fore.BLACK + Back.GREEN + begin_date.strftime("%d/%m/%Y (%A)"))  # Begin of week

approve('This program will create forum topics for this week.')

LOGIN_URL = 'https://sdo.rgsu.net/index/authorization/role/guest/mode/view/name/Authorization'
TUTOR_URL = 'https://sdo.rgsu.net/switch/role/tutor'
URL = 'https://sdo.rgsu.net'

# =============================================================================
# Create payload
# =============================================================================
SETTINGS = get_settings('settings.txt')
payload = {
    "start_login": 1,
    "login": SETTINGS[0].strip(),
    "password": SETTINGS[1].strip()
}
# HTTP headers for sdo.rgsu.net
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0',
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': URL,
    'Connection': 'keep-alive',
    'Referer': 'https://sdo.rgsu.net/'}

sdo = requests.session()

# Perform login
response = sdo.post(LOGIN_URL, data=payload, headers=headers)
if response.ok and ('Пользователь успешно авторизован.' in response.text):
    print('Login OK!')
else:
    raise Exception('Login failed! Check settings.')
response = sdo.get(TUTOR_URL, headers=headers)
if response.ok:
    print('Tutor mode ON!')
else:
    raise Exception('Connection not established. Try again.')

# =============================================================================
# Create forum topics for all groups in timetable
# =============================================================================
timetable = read_data(begin_date)
print("Let's make forum topics!")
print('Progress: |' + Back.WHITE + ' ' * 50 + Back.RESET + '|   0%', end='')
for i, lesson in enumerate(timetable):
    topic_title = f'Отметка посещения {lesson["group"]}: {lesson["time"].strftime("%d.%m.%Y")}, ' + \
                  f'время занятия {lesson["time"].strftime("%H:%M")}-' + \
                  (lesson['time'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") + f' ({lesson["type"]})'
    topic_text = f'<p><span style="font-size: x-large;">Группа {lesson["group"]}, это тема только ' + \
                 f'для отметки посещения пары с {lesson["time"].strftime("%H:%M")} по ' + \
                 (lesson['time'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") + '!</span></p>' + \
                 '<p>Отметка производится <strong>строго</strong> во время занятия ' + \
                 '(<strong>автоматически проверяется дата и время создания сообщения</strong>). ' + \
                 '<strong>Сообщения об отметке НЕ во время занятия НЕ учитываются</strong>. ' + \
                 'Просьба написать в данной теме <strong>только одно</strong> сообщение и <strong>только, ' + \
                 'если вы присутствуете на занятии</strong> (преподаватель производит сверку ваших отметок ' + \
                 'со списком подключенных к трансляции).</p><p><strong>Создайте сообщение </strong></p>' + \
                 '<ul><li><strong>В заголовке:</strong> присутствовал(а)</li>' + \
                 '<li><strong>В сообщении:</strong> присутствовал(а)</li></ul>'
    payload = {'title': topic_title, 'text': topic_text}
    headers['Referer'] = lesson['forum']
    response = sdo.post(lesson['forum'] + '/0/newtheme/create', data=payload, headers=headers)
    if not response.ok:
        print(f"\rCan't create topic for {lesson['group']}. See {lesson['forum']}.")
    s = int(50 * (i + 1) / len(timetable) + 0.5)
    print('\rProgress: |' + Back.BLUE + '#' * s + Back.WHITE + ' ' * (50 - s) + Back.RESET + f'| {2 * s:>4}%', end='')
print('\rProgress: |' + Back.BLUE + '#' * 50 + Back.RESET + '| ' + Fore.GREEN + '100% ')
print('All work is done!')
# input('press enter...')
