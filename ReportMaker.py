from datetime import datetime, timedelta
import sys, time
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.chrome.options import Options # for Chrome browser

try:
    with open('settings.txt', encoding='utf8') as f:
        settings = f.readlines()
except(IOError, OSError) as e:
    print(e)
    print()
    sys.exit('Error when reading settings.txt !!! Check also file encoding.')

f_date = list(map(int, settings[0].strip().split('.')))
date = datetime(f_date[2], f_date[1], f_date[0], 23, 59, 59)
date_str = date.strftime("%d.%m.%y")
print('Date of report:', date_str)
login = settings[1].strip()
password = settings[2].strip()

date_wd = datetime.now()
while date_wd.isoweekday() != 1:
    date_wd -= timedelta(1)
if date < date_wd or date - date_wd > timedelta(6):
    sys.exit('Error!!! Check date in settings.txt')

def mymes(mes, d):
    k = 80 - len(mes) - 7
    print(mes + '...', end='')
    for i in range(k):
        print('.', end='')
        sleep(d / k) 
    print('.[+]')

def count_students(group_name, rd2): # count students on downloaded attendance page, using last rd2 columns
    select_group = driver.find_element_by_xpath('//*[@id="groupname"]')
    for list_item in select_group.find_elements_by_tag_name("option"): # cycle throuh elements in drop-down list to find our group
        if group_name in list_item.text: # if group is founded, open journal and counting attendance
            select_group.click()                 # click dropdown list
            list_item.click()                    # click group
            print(list_item.text)
            break
    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[1]/div/div/div/form[1]/div/div[2]/button').click() # filter button click
    try:
        get_link = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="marksheet-form-filters"]/div/div[3]/div/a[3]/div'))) # all link click
        get_link.click()
    except:
        print('Check attendance page! There is no link "all" for', group_name)
    j_dates = []
    flag = False
    element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[1]/div/div/div/form[2]/table/thead/tr')))
    for jd in element.find_elements_by_tag_name('th')[1:-2]:
        tmp = jd.find_element_by_class_name("date-caption").text.strip().split('.')
        tmp = datetime(int(tmp[2]), int(tmp[1]), int(tmp[0]))
        if len(j_dates) != 0 and tmp < j_dates[-1][0]: # ok, it is last date of checking
            break
        if len(j_dates) != 0 and tmp > j_dates[-1][0]: # if dates growing then journal not new
            flag = True
        j_dates.append([tmp, jd])
    if not flag: # if we reach last date in period and all dates equals, then we need count since first columns
        j_dates = j_dates[:rd2]
    rd7 = []
    for i in range(rd2):
        id_th_day = j_dates[i - rd2][1].get_attribute('id')[7:] # take id of date to count cells by id
        count = 0
        for td in driver.find_elements_by_class_name('is_be_row_' + id_th_day):
            if td.find_element_by_tag_name('p').text.strip() == 'Был':
                count += 1
        rd7.append(count) # append attendance in array
    return rd7

opts = Options()  
opts.add_argument("--headless")
opts.add_argument('--ignore-certificate-errors')
#opts.page_load_strategy = 'normal'
print('Driver is starting now .........................................................')
print("Please wait, don't close windows! ..............................................")

# Download driver on https://github.com/mozilla/geckodriver/releases
driver = webdriver.Firefox(options=opts, executable_path=r'geckodriver.exe')

# Download Chrome driver if you use Google Chrome
# https://sites.google.com/a/chromium.org/chromedriver/home
#driver = webdriver.Chrome(chrome_options=opts, executable_path=r'chromedriver.exe')  

#driver.implicitly_wait(10) # seconds
wait = WebDriverWait(driver, 20)

print('Headless Mode is initialized ................................................[+]')
driver.get('https://sdo.rgsu.net/')
get_link = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'login')))
get_link.click()
mymes('Opening login form', 1)
mymes('Entering login and password', 1)
driver.find_element_by_id('login').send_keys(login) 
driver.find_element_by_id('password').send_keys(password)  
get_link = wait.until(EC.element_to_be_clickable((By.ID, 'submit'))) # submit authorization
get_link.click()

get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/span/div/span[2]/span/div/div[2]'))) # tutor mode ON
get_link.click()

driver.maximize_window()

get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/ul/li[7]/a'))) # go to timetable and parse it
get_link.click()

mymes('Timetable is opening',2)
print('Parsing.........................................................................')
pairs = driver.find_elements_by_class_name("tt-row")
tt_row = 0    # rows counter in time table
pair_num = 0  # счётчик пар - номер пары по счёту в этот день = числу видеофайлов, которые будут загружаться - сделать проверку!!!!
report_data = [] # array of data
for pair in pairs:
    pair_cells = pair.find_elements_by_tag_name('td') # распарсиваем строчку в расписании на отдельные ячейки
    if date_str in pair_cells[2].text.strip(): # заданная дата в ячейке -> надо заполнить отчёт
        # переделать в словарь!!!
        # +собираем данные для отчёта ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++:
        #0-tt_row, номер пары, пар с группой, 3-группа, тип пары, 5-время начала, время окончания, 7-посещения, 8-ссыль на журнал, 9-newspage, 10-videolink, 11 - newslink
        group = pair_cells[3].text.strip() # группа
        group_num = 1 # счётчик пар с конкретной группой - надо делать проверку текущего массива по этому индексу и инкрементить индекс
        lesson_type = pair_cells[4].text.strip() # тип занятия
        #p = re.compile(r'\d+')
        #hmhm = p.findall(pair_cells[0].text.strip())
        hmhm = pair_cells[0].text.strip()
        try:
            lesson_time = [hmhm[:5], hmhm[8:]] # время пары
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

# заходим на страницу с курсами СДО, парсим ссылки на ПОСЕЩЕНИЯ + КУРС
print('Script working. Please, wait ...................................................')
driver.get(driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/ul/li[2]/a').get_attribute('href'))
mymes('Loading data', 5)
for les_data in report_data:
    #находим группу и парсим ссылку на страничку с посещениями
    for lesson in driver.find_elements_by_class_name("lesson_table"):
        group = lesson.find_elements_by_tag_name('p')[5].text # Мои курсы - группы в курсе - мы перебираем и
        if les_data[3] in group: # проверяем, что группа тут, тогда будем искасть в боковом фрейме ссылку на журнал посещений
            # поиск ссылки на lesson_type журнал
            for items in lesson.find_elements_by_class_name("hm-subject-list-item-description-lesson-title"):
                link_elem = items.find_element_by_tag_name('a')
                if les_data[4][:6] in link_elem.text: # если тип занятия совпадает
                    les_data[8] = link_elem.get_attribute('href') # сохраняем ссылку на журнал посещений
                    break # нашли ссылку, сохранили и вышли из цикла поиска
            break # выходим из цикла поиска ссылок для группы, переходим к другой группе
# let's go to attendance page of current lesson type
#flag = False # flag to skip handled group
for les_data in report_data:
    if les_data[9] == '':       # no link to news page, therefore need to handle group
        driver.get(les_data[8]) # go to attendance page
        mymes('Loading journal', 1)
        les_data[9] = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[2]/div/div[5]/div/ul/li[1]/ul/li[1]/a').get_attribute('href') # News link
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[3]').click() # close meny panel
        les_data[7] = count_students(les_data[3], les_data[2])
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[3]').click() # open meny panel
    if les_data[2] > 1:
        for les_data1 in report_data:
            if les_data[3] == les_data1[3] and les_data1[9] == '':
                les_data1[7] = les_data[7]
                les_data1[9] = les_data[9]

#les_data = ['tt_row', 1, 3, 'group', 'lesson_type', 'lesson_time[0]', 'lesson_time[1]', [], '', '', 'http://google.com/', '']
#
# loading video files on sdo cloud
# пока просто заглушка - читаем ссылки на файлы в облаке из файла
for lesson in report_data:
    #print(lesson)
    lesson[10] = settings[lesson[1] + 3].strip()
# here must be block for uploading video files to cloud.rssu.net

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
                news_text += '<li><a href="' + les_data1[10] + '">Запись трасляции занятия</a>&nbsp;(' + les_data1[4] + ',&nbsp;' + les_data1[5] + ' - ' + les_data1[6] + ')'
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
        get_link = wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[1]/div/div/div/div[3]/div/div/div[1]/div[2]/a')))
        mymes('Saving news', 1)
        les_data[11] = get_link.get_attribute('href')
        if les_data[2] > 1:
            for les_data1 in report_data:
                if les_data[3] == les_data1[3] and les_data1[11] == '':
                    les_data1[11] = les_data[11]

# Open timetable page to write report        
get_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main"]/div[1]/div/ul/li[7]/a')))
get_link.click()
for les_data in report_data:
    pairs = driver.find_elements_by_class_name("tt-row")
    report_button = pairs[les_data[0]].find_element_by_tag_name('button')
    driver.execute_script('arguments[0].scrollIntoView({block: "center"})', report_button)
    mymes('Scrolling page', 2)
    report_button.click()
    driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/div/form/dl/dd[1]/input').send_keys(Keys.BACKSPACE + str(les_data[7][0]))
    driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/div/form/dl/dd[2]/input').send_keys(Keys.BACKSPACE + les_data[10])
    driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/div/form/dl/dd[3]/input').send_keys(Keys.BACKSPACE + les_data[11])
    driver.find_element_by_xpath('/html/body/div[3]/div[3]/div/button[1]/span').click()

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
#input('press any key...')
driver.quit()
print("Driver Turned Off")
