from datetime import datetime, timedelta
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

login = settings[1].strip()
password = settings[2].strip()
token = settings[3].strip()
video_path = settings[4].strip()
browser = settings[5].strip().upper()
browser_driver_path = settings[6].strip()

date = [int(x) for x in settings[0].strip().split('.')[::-1]]
date = datetime(*date, 23, 59, 59)
date_str = date.strftime("%d.%m.%y")
print('Date of report:', date_str)

date_wd = datetime.now()
while date_wd.isoweekday() != 1:
    date_wd -= timedelta(1)
if date < date_wd or date - date_wd > timedelta(6):
    sys.exit('Error!!! Check date in settings.txt')

def mymes(mes, d, plus_mark = True):
    k = 80 - len(mes) - 7
    print(mes + '...', end='')
    for i in range(k):
        print('.', end='')
        sleep(d / k) 
    if plus_mark:
        print('.[+]')
    else:
        print('....')

def count_students(group_name, rd2): 
    '''Count students on downloaded attendance page, using last rd2 columns.'''
    select_group = driver.find_element_by_xpath('//*[@id="groupname"]')
    # cycle throuh elements in drop-down list to find our group
    for list_item in select_group.find_elements_by_tag_name("option"): 
        # if group is founded, open journal and counting attendance
        if group_name in list_item.text: 
            select_group.click()         # click dropdown list
            list_item.click()            # click group
            print(list_item.text)
            break
    driver.find_element_by_xpath('//*[@id="marksheet-form-filters"]/div/div[2]/button').click() # filter button click
    get_link = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="ending"]'))) # all link click
    get_link.click()
    j_dates = []
    flag = False
    # Get head of journal table:
    element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="journal"]/table/thead/tr')))
    for jd in element.find_elements_by_tag_name('th')[1:-2]:
        tmp = jd.find_element_by_class_name("date-caption").text.strip().split('.')
        tmp = datetime(int(tmp[2]), int(tmp[1]), int(tmp[0]))
        if len(j_dates) != 0 and tmp < j_dates[-1][0]: 
            # ok, it is last date of checking
            break
        if len(j_dates) != 0 and tmp > j_dates[-1][0]: 
            # if dates growing then journal not new
            flag = True
        j_dates.append([tmp, jd])
    if not flag: 
        # if we reach last date in period and all dates equals, 
        # then we need count first columns
        j_dates = j_dates[:rd2]
    rd7 = []
    for i in range(rd2):
        id_th_day = j_dates[i - rd2][1].get_attribute('id')[7:] 
        # take id of date to count cells by id
        count = 0
        for td in driver.find_elements_by_class_name('is_be_row_' + id_th_day):
            if td.find_element_by_tag_name('p').text.strip() == 'Был':
                count += 1
        rd7.append(count) # append attendance in array
    return rd7

# =============================================================================
# Browser driver inicialization
# =============================================================================
if browser[0] == 'F':
    from selenium.webdriver.firefox.options import Options # for Firefox browser
elif browser[0] == 'C' or browser[0] == 'G':
    from selenium.webdriver.chrome.options import Options # for Chrome browser

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

#driver = webdriver.Safari(executable_path = r'/usr/bin/safaridriver') # for MacOS

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
mymes('Parsing', 1, False)
pairs = driver.find_elements_by_class_name("tt-row")
tt_row = 0    # rows counter in time table
pair_num = 0  # pair counter - номер пары по счёту в этот день 
report_data = [] # array of data
for pair in pairs:
    # распарсиваем строчку в расписании на отдельные ячейки
    pair_cells = pair.find_elements_by_tag_name('td') 
    # заданная дата в ячейке -> надо заполнить отчёт
    if date_str in pair_cells[2].text.strip(): 
        # переделать в словарь!!!
        # +собираем данные для отчёта ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++:
        #0-tt_row, номер пары, пар с группой, 3-группа, тип пары, 5-время начала, время окончания, 7-посещения, 8-ссыль на журнал, 9-newspage, 10-videolink, 11 - newslink
        group = pair_cells[3].text.strip() # группа
        group_num = 1 # счётчик пар с конкретной группой - надо делать проверку текущего массива по этому индексу и инкрементить индекс
        lesson_type = pair_cells[4].text.strip() # lesson type
        hmhm = pair_cells[0].text.strip()
        try:
            lesson_time = [hmhm[:5], hmhm[8:]] # time of lesson
        except:
            print('Bad time format: [ {} ]'.format(pair_cells[0].text.strip()))
            print('Check time for:', group, pair_cells[5].text.strip(), pair_cells[6].text.strip())
            lesson_time = ['22:15', '23:45']
        # проверка того, что предыдущая запись в таблице - пара в то же время, при несовпадении увеличиваем счётчик pair_num
        if len(report_data) == 0 or report_data[-1][5] != lesson_time[0]:
            pair_num += 1
        # подсчёт количества пар с группой
        for rep in report_data:
            if rep[3] == group:
                rep[2] += 1
                group_num = rep[2]
        # пишем все данные в список и добавляем список в конец массива report_data:
        report_data.append([tt_row, pair_num, group_num, group, lesson_type, lesson_time[0], lesson_time[1], [], '', '', '', ''])
    tt_row += 1

# =============================================================================
# Go to "My Courses" page - it loads very long !!!
# =============================================================================
mymes('Script working. Please, wait', 0, False)
driver.get(driver.find_element_by_xpath('//div[@class="wrapper"]/ul/li[2]/a').get_attribute('href'))
mymes('Loading All courses page', 1) # pause and wait until all elements located:
wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="credits"]')))
for les_data in report_data:
    # checking group and finding links to group's journal
    for lesson in driver.find_elements_by_class_name("lesson_table"):
        if les_data[3] in lesson.find_element_by_class_name("lesson_options").text: # checking that left table pane contains our group
            # finding link to journal of our lesson_type
            for items in lesson.find_elements_by_class_name("hm-subject-list-item-description-lesson-title"):
                link_elem = items.find_element_by_tag_name('a')
                if les_data[4][:6] in link_elem.text: # if lesson types matches
                    # save link to journal of attendance:
                    les_data[8] = link_elem.get_attribute('href')
                    break
            break # go to next group

# =============================================================================
# Let's go to attendance page of current lesson type
# =============================================================================
for les_data in report_data:
    if les_data[9] == '':       # no link to news page, therefore need to handle group
        driver.get(les_data[8]) # go to attendance page
        mymes('Loading journal', 1)
        # Get news link
        get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="activity-1"]')))
        les_data[9] = get_link.get_attribute('href')
        driver.find_element_by_xpath('//*[@id="main"]/div[3]').click() # close meny panel
        les_data[7] = count_students(les_data[3], les_data[2])
        driver.find_element_by_xpath('//*[@id="main"]/div[3]').click() # open meny panel
    if les_data[2] > 1:
        for les_data1 in report_data:
            if les_data[3] == les_data1[3] and les_data1[9] == '':
                les_data1[7] = les_data[7]
                les_data1[9] = les_data[9]

# =============================================================================
# Unloading video files on cloud.sdo.net
# =============================================================================
opts = {
 'webdav_hostname': token,
 'webdav_login':    login,
 'webdav_password': password,
 'verbose':         True
}
client = Client(opts) # using webdav protocol for files uploading

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

rem_folders = ['Запись занятий', date.strftime("%Y") + '_год', \
         date.strftime("%m") + '_месяц', date.strftime('%m_%d')]

rem_path = ''
for folder in rem_folders:
    rem_path += folder + '/'
    checkpath(rem_path)

files = os.listdir(video_path)
free_space()
print('upload cycle')
for file in files:
    if 'Video' in file:
        print('File {} is uploading now. Please, wait!!!'.format(file))
        client.upload_sync(remote_path = rem_path + '/' + file, \
        local_path = os.path.join(video_path, file))
        print('Uploading of {} is finished.'.format(file))
print('Uploading of all files is finished.')
free_space()

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
    video_links.append(link_button.get_attribute('href').strip()) # add link

for les_data in report_data:
    les_data[10] = video_links[les_data[1] - 1]

# =============================================================================
# Making news
# =============================================================================
for les_data in report_data:
    if les_data[11] == '': # если ещё не сделали новости и не записали ссылку на новость, то:
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
        mymes('Saving news', 1) # This timeout is no needed and can be commented or deleted!
        get_link = wait.until(EC.presence_of_element_located((By.XPATH,'//a[contains(text(), "Видеоматериалы занятия от")]')))
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
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', report_button)
    mymes('Scrolling page', 2)
    report_button.click()
    driver.find_element_by_name("users").send_keys(Keys.BACKSPACE + str(les_data[7][0]))
    driver.find_element_by_name("file_path").send_keys(Keys.BACKSPACE + les_data[10])
    driver.find_element_by_name("subject_path").send_keys(Keys.BACKSPACE + les_data[11])
    driver.find_element_by_xpath('//div[@class="ui-dialog-buttonset"]/button[1]').click()

'''
print('This day you have next lessons:')
for lesson in report_data:
    print(lesson)
'''

f = open('report.txt', 'w')
f.write('This day you have next lessons\n\n')
f.write('N\ttime time\tlesson_type\tgroup\t students\t Link in cloud.sdo.net\t Link in news\n\n')
for lesson in report_data:
    f.write(str(lesson[1])+'\t'+lesson[5]+' '+lesson[6]+'\t'+lesson[3]+'\t'+lesson[4]+'\t '+str(lesson[7])+' '+lesson[10]+' '+lesson[11]+'\n\n')
f.close()

print("All work is done! Congratulations!!!!!!!!!")
#input('press enter...')
driver.quit()
print("Driver Turned Off")
