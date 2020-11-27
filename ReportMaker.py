#!/usr/bin/env python3
# Volodin Yuriy, 2020
# volodinjuv@rgsu.net
# Making teacher's report on SDO.RSSU.NET
# ==================== Version 2.0 ===========================================
import re
from datetime import datetime, timedelta
from infoout import mymes
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import sys
from time import sleep
from webdav3.client import Client
# ============================================================================

try:
    with open('settings.txt', encoding='utf8') as f:
        settings = f.readlines()
except(IOError, OSError) as e:
    print(e)
    print()
    sys.exit('Error when reading settings.txt !!! Check also file encoding.')

login = settings[0].strip()
password = settings[1].strip()
token = settings[2].strip()
video_path = settings[3].strip()
browser = settings[4].strip().upper()
browser_driver_path = settings[5].strip()

date_wd = datetime.now()
if len(sys.argv) < 2:
    date = date_wd
else:
    date = [int(x) for x in sys.argv[1].split('.')[::-1]]
    if date[0] < 50:
        date[0] = 2000 + date[0]
    date = datetime(*date, 23, 59, 59)
date_str = date.strftime("%d.%m.%y")
print('Date of report:', date_str)

while date_wd.isoweekday() != 1:
    date_wd -= timedelta(1)
if date < date_wd or date - date_wd > timedelta(6):
    sys.exit('Error! Cannot make a report for this date. Check date in settings.txt')


def scroll_page(web_element, t=2):
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', web_element)
    sleep(t)


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
# Go to timetable and parse it:
# =============================================================================
get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="wrapper"]/ul/li[7]/a')))
get_link.click()

mymes('Timetable is opening', 1)
pairs = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "tt-row")))
progress_l = 80 - 14 - 2
print('Parsing: [' + ' ' * progress_l + '] 0%', end='')
tt_row = 0  # rows counter in time table
pair_num = 0  # pair counter - номер пары по счёту в этот день 
report_data = []  # array of data
for pair in pairs:
    # Read lines, parse discipline, time, date and type
    pair_cells = pair.find_elements_by_tag_name('td')
    # if date on current line in cell 3 - it is our date
    cell3 = pair_cells[2].text  # discipline and dates in a single cell
    if date_str in cell3:
        group = pair_cells[3].text.strip()  # группа
        group_num = 1  # счётчик пар с конкретной группой
        lesson_type = pair_cells[4].text.strip()  # lesson type
        discipline = re.sub(r'\s?\d{2}.\d{2}.(\d{2}|\d{4});?', '', cell3).strip()
        try:
            cell_date = date.replace(hour=int(pair_cells[0].text.strip()[:2]),
                                     minute=int(pair_cells[0].text.strip()[3:5]),
                                     second=0, microsecond=0)
        except:
            print('Bad time format: [ {} ]'.format(pair_cells[0].text.strip()[3:5]))
            print('Check time for:', group, pair_cells[5].text.strip(), pair_cells[6].text.strip())
            cell_date = date.replace(hour=8, minute=0, second=0, microsecond=0)
        # проверка, что предыдущая запись в таблице - пара в то же время, при несовпадении увеличиваем счётчик pair_num
        if len(report_data) == 0 or \
                report_data[-1]['date'].hour != date.hour or report_data[-1]['date'].minute != date.minute:
            pair_num += 1
        # подсчёт количества пар с группой
        for rep in report_data:
            if rep['group'] == group:
                rep['group_n'] += 1
                group_num = rep['group_n']
        # пишем все данные в список и добавляем список в конец массива report_data:
        report_data.append({'row': tt_row, 'pair': pair_num,
                            'group_n': group_num, 'group': group,
                            'type': lesson_type, 'discipline': discipline,
                            'date': cell_date, 'news': ''})
    tt_row += 1
    print('\rParsing: [' + '#' * (tt_row * progress_l // len(pairs)) +
          ' ' * ((len(pairs) - tt_row) * progress_l // len(pairs)) + '] ' +
          str(int(tt_row / len(pairs) * 100 + 0.5)) + '%', end='')

print('\rParsing: [' + '#' * progress_l + '] 100%')

# =============================================================================
# Go to "My Courses" page - it downloads very long !!!
# =============================================================================
mymes('Script working. Please, wait', 0, False)
driver.get(driver.find_element_by_xpath('//div[@class="wrapper"]/ul/li[2]/a').get_attribute('href'))
mymes('Loading All courses page', 1)  # pause and wait until all elements located:
wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="credits"]')))  # checking that page is downloaded
progress_l = 80 - 14 - 2
progress = 0
print('Parsing: [' + ' ' * progress_l + '] 0%', end='')
for les_data in report_data:
    # checking group and finding links to group's journal
    for lesson in driver.find_elements_by_class_name("lesson_table"):
        # checking that left table pane contains our group:
        if les_data['group'] in lesson.find_element_by_class_name("lesson_options").text:
            # finding link to page of this course
            link = lesson.find_element_by_id("lesson_title").find_element_by_tag_name('a').get_attribute('href')
            course_id = re.search(r'\d+$', link)[0]
            les_data['news'] = 'https://sdo.rgsu.net/news/index/index/subject_id/' + course_id + '/subject/subject'
            les_data['forum'] = 'https://sdo.rgsu.net/forum/subject/subject/' + course_id
            # finding link to journal of our lesson_type
            for items in lesson.find_elements_by_class_name("hm-subject-list-item-description-lesson-title"):
                link_elem = items.find_element_by_tag_name('a')
                if les_data['type'][:6] in link_elem.text:  # if lesson types matches
                    # save link to journal of attendance:
                    les_data['journal'] = link_elem.get_attribute('href') + '/day/all'
                    break
            break  # go to next group
    progress += 1
    print('\rParsing: [' + '#' * (progress * progress_l // len(report_data)) +
          ' ' * ((len(report_data) - progress) * progress_l // len(report_data)) + '] ' +
          str(int(progress / len(report_data) * 100 + 0.5)) + '%', end='')
print('\rParsing: [' + '#' * progress_l + '] 100%')

print('This day you have next lessons:')
for les_data in report_data:
    print(les_data)

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
        if les_data['date'].strftime("%d.%m.%Y") in topic_title and les_data['date'].strftime("%H:%M") in topic_title:
            element = topic.find_element_by_class_name('topic-expand-comments')
            scroll_page(element)
            element.click() # expand all comments
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
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main"]/div[3]')))
    element.click()  # close menu panel
    # Open drop-down menu
    select_group = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="groupname"]')))
    # cycle through elements in drop-down list to find our group
    for list_item in select_group.find_elements_by_tag_name("option"):
        # if group is founded, open journal and counting attendance
        if les_data['group'] in list_item.text:
            select_group.click()  # click dropdown list
            list_item.click()  # click group
            print(list_item.text)  # Print selected group name
            break
    driver.find_element_by_xpath('//*[@id="marksheet-form-filters"]/div/div[2]/button').click()  # filter button click
    # get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "/day/all")]')))  # all link
    # driver.get(get_link.get_attribute('href'))
    mymes('Filling attendance of students', 1, False)
    # ###########################################################################################################
    # Get head of journal table:
    table_head = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="journal"]/table/thead/tr')))
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
    # input("press enter:")
    # element.click()  # FIXME
    # Cycle


for les_data in report_data:
    print(les_data)

'''
# =============================================================================
# FIXME Unloading video files on cloud.sdo.net  - async uploading!!!
# =============================================================================
opts = {
    'webdav_hostname': token,
    'webdav_login': login,
    'webdav_password': password,
}
client = Client(opts)  # using webdav protocol for files uploading

mymes('WebDAV client initialized', 0)


def free_space():
    fs = float(client.free())
    for i in range(3):
        fs /= 1024
    print('Free space in your cloud: {0:.2f} Gb'.format(fs))


def checkpath(p):
    if not client.check(p):
        client.mkdir(p)
        print('Directory [{}] created.'.format(p))


rem_folders = ['Запись занятий', date.strftime("%Y") + '_год', date.strftime("%m") + '_месяц', date.strftime('%m_%d')]

rem_path = ''
for folder in rem_folders:
    rem_path += folder + '/'
    checkpath(rem_path)

files = os.listdir(video_path)
free_space()
mymes('Upload cycle', 0, False)
for file in files:
    if 'Video' in file:
        print('File {} is uploading now. Please, wait!!!'.format(file))
        client.upload_sync(remote_path=rem_path + '/' + file,
                           local_path=os.path.join(video_path, file))
        mymes('Uploading of ' + file + ' is finished', 0)
mymes('Uploading of all files is finished', 0)
free_space()

# =============================================================================
# Generating links for files on cloud.sdo.net through web interface
# =============================================================================

mymes('Now links will be generated through web interface.', 0, False)
driver.get('https://cloud.rgsu.net/')
mymes('Entering login and password', 1)
driver.find_element_by_id('user').send_keys(login)
driver.find_element_by_id('password').send_keys(password)
driver.find_element_by_id('submit-form').click()
mymes('Authorization', 1)

driver.get('https://cloud.rgsu.net/apps/files/?dir=/' + '/'.join(rem_folders))
fileList = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="fileList"]')))
video_links = []
share_buttons = fileList.find_elements_by_xpath('//td[2]/a/span[2]/a[1]/span[1]')
for b in share_buttons:
    b.click()
    mymes('Sharing file', 2)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sharing"]/ul[1]/li/button'))).click()
    # One click somewhere to close menu:
    driver.find_element_by_xpath('//*[@id="filestable"]/tfoot/tr/td[2]/span/span[3]').click()
    link_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//ul[@class="sharing-link-list"]/li/a')))
    video_links.append(link_button.get_attribute('href').strip())  # add link

for les_data in report_data:
    les_data[10] = video_links[les_data[1] - 1]

# =============================================================================
# Making news
# =============================================================================
for les_data in report_data:
    if les_data[11] == '':  # если ещё не сделали новости и не записали ссылку на новость, то:
        driver.get(les_data[9])
        mymes('Loading news page', 2)
        driver.find_element_by_partial_link_text('Создать новость').click()
        mymes('Loading news form', 2)
        driver.find_element_by_tag_name("html").send_keys(Keys.PAGE_DOWN)
        announce = 'Видеоматериалы занятия от ' + date.strftime("%d.%m.%Y") + ' с группой ' + les_data[3]
        news_text = '<p>Занятие от ' + date.strftime("%d.%m.%Y") + ' г.:</p><ul>'
        for les_data1 in report_data:
            if les_data[3] == les_data1[3]:
                news_text += '<li><a href="' + les_data1[10] + '">Запись трасляции занятия</a>&nbsp;(' \
                             + les_data1[4] + ',&nbsp;' + les_data1[5] + ' - ' + les_data1[6] + ')'
        news_text += '</ul>'
        get_link = wait.until(EC.presence_of_element_located((By.ID, 'announce')))
        get_link.send_keys(announce)
        get_link = wait.until(EC.presence_of_element_located((By.ID, 'message_code')))
        get_link.click()
        mymes('Loading edit form', 1)
        driver.switch_to.frame("mce_13_ifr")
        driver.find_element_by_xpath('//*[@id="htmlSource"]').send_keys(news_text)
        driver.find_element_by_id('insert').click()
        driver.switch_to.default_content()
        driver.find_element_by_id('submit').click()
        mymes('Saving news', 1)  # This timeout is no needed and can be commented or deleted!
        get_link = wait.until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "Видеоматериалы занятия от")]')))
        les_data[11] = get_link.get_attribute('href')
        if les_data[2] > 1:
            for les_data1 in report_data:
                if les_data[3] == les_data1[3] and les_data1[11] == '':
                    les_data1[11] = les_data[11]

# =============================================================================
# Open timetable page to write report        
# =============================================================================
get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main"]/div[1]/div/ul/li[7]/a')))
get_link.click()
for les_data in report_data:
    pairs = driver.find_elements_by_class_name("tt-row")
    report_button = pairs[les_data[0]].find_element_by_tag_name('button')
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', report_button)  # REFACTOR
    mymes('Adding report', 2)
    report_button.click()
    driver.find_element_by_name("users").send_keys(Keys.BACKSPACE + str(les_data[7][0]))
    driver.find_element_by_name("file_path").send_keys(Keys.BACKSPACE + les_data[10])
    driver.find_element_by_name("subject_path").send_keys(Keys.BACKSPACE + les_data[11])
    driver.find_element_by_xpath('//div[@class="ui-dialog-buttonset"]/button[1]').click()

'''
'''
print('This day you have next lessons:')
for lesson in report_data:
    print(lesson)
'''
'''
f = open('report.txt', 'w')
f.write('This day you have next lessons\n\n')
f.write('N\ttime time\tlesson_type\tgroup\t students\t Link in cloud.sdo.net\t Link in news\n\n')
for lesson in report_data:
    f.write(str(lesson[1]) + '\t' + lesson[5] + ' ' + lesson[6] + '\t' + lesson[3] + '\t' + lesson[4] + '\t ' + str(
        lesson[7]) + ' ' + lesson[10] + ' ' + lesson[11] + '\n\n')
f.close()
'''

print("All work is done! See program report in report.txt")
# input('press enter...')
driver.quit()
print("Driver Turned Off")
