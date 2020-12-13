#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ========================== Version 3.3 ==============================================
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
from colorama import Back
from datetime import timedelta
from sdodriver.infoout import *
from sdodriver import edge as sdo
import sys

login, password, _, _, browser, browser_driver_path = map(str.strip, get_settings('settings.txt'))

begin_date = datetime.now()
if len(sys.argv) > 1 and sys.argv[1] == 'n':  # if parameter n in command line
    begin_date += timedelta(7)

# List of days in the week
while begin_date.isoweekday() != 1:
    begin_date -= timedelta(1)
print('Begin of week: ', Fore.BLACK + Back.GREEN + begin_date.strftime("%d/%m/%Y (%A)"))  # begin of week
week_dates = [begin_date + timedelta(i) for i in range(6)]

timetable = read_data(begin_date)
# sorting by URL to minimize page reloads and then by pair to chronological order of topics:
timetable.sort(key=lambda les: (les['forum'], -les['pair']))

# Browser driver initialization
mymes("Driver is starting now. Please wait, don't close windows!", 0, False)
driver = sdo.Driver(browser, browser_driver_path)
# Login on sdo.rgsu.net
mymes('Login on [sdo.rgsu.net]', 0, False)
driver.open_sdo(login, password)

# =============================================================================
# Create forum topics for all groups in timetable
# =============================================================================
k = 0
last_forum = ''
mymes("Let's make forum topics!", 0, False)
for lesson in timetable:
    if lesson['forum'] != last_forum:
        driver.get(lesson['forum'])
        last_forum = lesson['forum']
    get_element = driver.find_element_by_xpath('//a[text()="Создать тему"]')
    driver.scroll_page(get_element, 0)
    mymes(f'Generating forum topic for group {lesson["group"]} ({lesson["time"].strftime("%H:%M")})', 2, False)
    get_element.click()
    get_element = driver.find_element_by_xpath('//div[@class="topic-input"]/input')
    driver.scroll_page(get_element, 0.3)
    # Отметка посещения [ГРУППА]: [ДАТА], время занятия [НАЧАЛО]-[КОНЕЦ] ([Лабораторная работа])
    get_element.send_keys(f'Отметка посещения {lesson["group"]}: {lesson["time"].strftime("%d.%m.%Y")}, ' +
                          f'время занятия {lesson["time"].strftime("%H:%M")}-' +
                          (lesson['time'] + timedelta(hours=1, minutes=30)).strftime("%H:%M") +
                          f' ({lesson["type"]})')
    driver.find_element_by_xpath('//a[@title="Редактировать HTML код"]').click()
    frame_id = driver.find_element_by_xpath('//iframe[starts-with(@id, "mce_")]').get_attribute('id')
    driver.switch_to.frame(frame_id)
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
    mymes('Filling form', 1)
    driver.find_element_by_id('htmlSource').send_keys(topic_text)
    driver.find_element_by_id('insert').click()
    driver.switch_to.default_content()
    get_element = driver.find_element_by_id('submit')
    # get_element = driver.find_element_by_xpath('//a/span[text()="Отменить"]')  # for DEBUG only!!!
    driver.scroll_page(get_element, 0.5)
    get_element.click()
    k += 1
    mymes(f'Saving topic {k} of {len(timetable)} ({k / len(timetable) * 100:.0f}%)', 1)

print(Fore.GREEN + "All work is done!")
# input('press enter...')
driver.turnoff()
