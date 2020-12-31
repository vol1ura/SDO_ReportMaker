#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ========================== Version 3.32 =====================================
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
from sdodriver.infoout import *
from sdodriver.sdo_requests import Session
import sys


begin_date = datetime.now()
if len(sys.argv) > 1 and sys.argv[1] == 'n':  # if parameter n in command line
    begin_date += timedelta(7)

while begin_date.isoweekday() != 1:
    begin_date -= timedelta(1)
print('Begin of week: ', Fore.BLACK + Back.GREEN + begin_date.strftime("%d/%m/%Y (%A)"))  # Begin of week

approve('This program will create forum topics.')

SETTINGS = get_settings('settings.txt')
sdo = Session(SETTINGS[0].strip(), SETTINGS[1].strip())

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
    response = sdo.make_topic(topic_title, topic_text, lesson['forum'])
    if not response.ok:
        print(Back.RED + f"\rCan't create topic for {lesson['group']}. See {lesson['forum']}.")
    s = int(50 * (i + 1) / len(timetable) + 0.5)
    print('\rProgress: |' + Back.BLUE + '#' * s + Back.WHITE + ' ' * (50 - s) + Back.RESET + f'| {2 * s:>4}%', end='')
print('\rProgress: |' + Back.BLUE + '#' * 50 + Back.RESET + '| ' + Fore.GREEN + '100% ')
print('All work is done!')
# input('press enter...')
