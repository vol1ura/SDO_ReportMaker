from bs4 import BeautifulSoup # Install it if you need: pip3 install beatifulsoup
#import csv                    # Install it if you need: pip3 install csv
from datetime import datetime, timedelta
import locale
import re

import sys, time
from time import sleep

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.chrome.options import Options # for Chrome browser

locale.setlocale(locale.LC_ALL, "")
try:
    f = open('settings.txt', encoding='utf8')
    try:
        teacher = '+'.join(f.readline().strip().split(' ')) # not used parameter!!!!
        f_date = list(map(int, f.readline().strip().split('.')))
        date = datetime(f_date[2], f_date[1], f_date[0], 23, 59, 59)
        date_str = date.strftime("%d.%m.%y")
        print('Date of report:', date_str)
        login = f.readline().strip()
        password = f.readline().strip()
    except Exception as e:
        print(e)
        print('Error!!! Check correctness of data and template in settings.txt!')
    finally:
        f.close()
except(IOError, OSError) as e:
    print(e)
    print()
    sys.exit('Error when reading settings.txt !!! Check also file encoding.')

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

def count_students(group_name, rd2): # на загруженной странице с посещаемостью подсчитываются посещения студентов группы в последних rd2 заполненных столбиках
    select_group = driver.find_element_by_xpath('//*[@id="groupname"]')
    for list_item in select_group.find_elements_by_tag_name("option"): # перебираем элементы в выпадающем списке, ищем группу, с которой провели пары
        if group_name in list_item.text: # если нашли эту группу, раскрываем журнал, находим последние заполненные даты и делаем в них подсчёт
            select_group.click()                 # кликаем выпадающий список
            list_item.click()                    # кликаем по нужной группе
            print(list_item.text)
            break
    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[1]/div/div/div/form[1]/div/div[2]/button').click() # filter button click
    mymes('Loading data', 2)
    try:
        driver.find_element_by_xpath('//*[@id="marksheet-form-filters"]/div/div[3]/div/a[3]/div').click() # all link click
        mymes('Loading data', 2)
    except:
        print('Warning! There is no all link for ', group_name)
    j_dates = []
    flag = False
    for jd in driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[1]/div/div/div/form[2]/table/thead/tr').find_elements_by_tag_name('th')[1:-2]:
        tmp = jd.find_element_by_class_name("date-caption").text.strip().split('.')
        tmp = datetime(int(tmp[2]), int(tmp[1]), int(tmp[0]))
        if len(j_dates) != 0 and tmp < j_dates[-1][0]: # всё, дошли до последней заполненной даты
            break
        if len(j_dates) != 0 and tmp > j_dates[-1][0]: # делаем проверку увеличения дат, т.е. журнал уже заполнялся
            flag = True
        j_dates.append([tmp, jd])
    if not flag: # дошли до конца диапазона дат, даты одинаковые, значит надо вести подсчёт в первых столбцах
        j_dates = j_dates[:rd2]
    # теперь забираем айдишники дат по которым пойдёт подсчёт. количество айдишков = количеству пар с группой
    print(len(j_dates))
    rd7 = []
    for i in range(rd2):
        print(j_dates[i - rd2][0])
        id_th_day = j_dates[i - rd2][1].get_attribute('id')[7:]
        count = 0
        # и подсчитываем посещение данной пары
        for td in driver.find_elements_by_class_name('is_be_row_' + id_th_day):
            if td.find_element_by_tag_name('p').text.strip() == 'Был':
                count += 1
        rd7.append(count) # надо записать значение в 7th элемент таблицы данных как массив
    return rd7

opts = Options()  
#opts.add_argument("--headless")
opts.add_argument('--ignore-certificate-errors')
print('Driver is starting now .........................................................')
print("Please wait, don't close windows! ..............................................")
# Download driver on https://github.com/mozilla/geckodriver/releases
driver = webdriver.Firefox(options=opts, executable_path=r'geckodriver.exe')

# Download Chrome driver if you use Google Chrome
# https://sites.google.com/a/chromium.org/chromedriver/home
#driver = webdriver.Chrome(chrome_options=opts, executable_path=r'chromedriver.exe')  

print('Headless Mode is initialized ................................................[+]')
driver.get('https://sdo.rgsu.net/')
mymes('Loading site [sdo.rgsu.net]. Please, wait', 1)
driver.find_element_by_class_name('login').click()
mymes('Opening login form', 1)
mymes('Entering login and password', 1)
driver.find_element_by_id('login').send_keys(login) 
driver.find_element_by_id('password').send_keys(password)  
driver.find_element_by_id('submit').click()
mymes('Authorization on [sdo.rgsu.net]. Please, wait', 3)
driver.find_element_by_xpath('/html/body/div[1]/div[1]/span/div/span[2]/span/div/div[2]').click()
mymes('Login on [sdo.rgsu.net]', 3)


driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/ul/li[7]/a/span').click()
#main_page = driver.current_window_handle
print('OK! Timetable is opened .....................................................[+]')
print('Parsing......................................................................[+]')
soup = BeautifulSoup(driver.page_source, 'lxml')
pairs = soup.find('tbody').find_all('tr')
#pairs = driver.find_elements_by_class_name("lesson")
tt_row = 0    # счётчик строк в таблице расписания
pair_num = 0  # счётчик пар - номер пары по счёту в этот день = числу видеофайлов, которые будут загружаться - сделать проверку!!!!
report_data = [] # массив данных:
for pair in pairs[1:]:
    pair_cells = pair.find_all('td') # распарсиваем строчку в расписании на отдельные ячейки
    if date_str in pair_cells[2].text.strip(): # заданная дата в ячейке -> надо заполнить отчёт
        # +собираем данные для отчёта ++++++++++++++:
        #0 tt_row, номер пары, пар с группой, 3-группа, тип пары, 5-время начала, время окончания, 7-посещения, 8-ссыль на журнал, 9-новости
        group = pair_cells[3].text.strip() # группа
        group_num = 1 # счётчик пар с конкретной группой - надо делать проверку текущего массива по этому индексу и инкрементить индекс
        lesson_type = pair_cells[4].text.strip() # тип занятия
        #xpath_rep_button = '/html/body/div[1]/div[2]/div[2]/div[2]/table/tbody/tr[' + str(tt_row + 2) + ']/td[9]/button/span' # кнопка отчёта - она пока тут не используется!!!!
        p = re.compile(r'\d+')
        hmhm = p.findall(pair_cells[0].text.strip()) # --------- soup !!!
        lesson_time = ['', ''] # время пары
        try:
            for i in range(2):
                lesson_time[i] += hmhm[2*i] + ':' + hmhm[1 + 2*i]
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
        report_data.append([tt_row, pair_num, group_num, group, lesson_type, lesson_time[0], lesson_time[1], [], '', ''])
    tt_row += 1
  
# Цикл:
# заходим на страницу с курсами СДО, парсим ссылки на ПОСЕЩЕНИЯ + КУРС
mycourses = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div/ul/li[2]/a').get_attribute('href') ### ссылка на страницу Мои курсы - нужна ли она???
print('Script working. Please, wait ...................................................')
driver.get(mycourses)
mymes('Loading data', 5)
#soup = BeautifulSoup(driver.page_source, 'lxml')  --- дальше не используем Прекрасный Суп. Надо обойтись без него и раньше
for les_data in report_data:
    #находим группу и парсим ссылку на страничку с посещениями
    i = 3
    while i < 200: # переделай цикл!!!!!!!!!!!!!!!
        xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div['+ str(i) + ']/div/div/div/div/table/tbody/tr'
        group = driver.find_element_by_xpath(xpath + '/td[2]/div[5]/p').text # Мои курсы - и-тый курс - группы в курсе - мы перебираем и
        if les_data[3] in group: # проверяем, что группа тут, тогда будем искасть в боковом фрейме ссылку на журнал посещений
            # ссылка на страничку курса - не нужна!!! Ссылку на страничку новости можно получить из журнала группы!
            #course_link = driver.find_element_by_xpath(xpath + '/td[2]/div[1]/a').get_attribute('href')
            # поиск ссылки на lesson_type журнал
            j = 1
            while j < 20: # переделать цикл - делать перебором по списку find_elements !!!!!
                link_elem = driver.find_element_by_xpath(xpath + '/td[4]/div/div[1]/ul/li[' + str(j) + ']/div[3]/a')
                if les_data[4][:6] in link_elem.text: # если тип занятия совпадает
                    les_data[8] = link_elem.get_attribute('href') # сохраняем ссылку на журнал посещений
                    break # нашли ссылку, сохранили и вышли из цикла поиска
                j += 1
            break # выходим из цикла поиска ссылок для группы, переходим к другой группе
        i += 1
# переходим в посещение лекций или семинаров или лабораторных,
flag = False # флаг для пропуска обработанных групп
for les_data in report_data:
    if les_data[9] == '': # если ещё не заполнили, открываем страничку с посещениями и считаем
        driver.get(les_data[8]) 
        mymes('Loading journal', 1)
        les_data[9] = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[2]/div/div[5]/div/ul/li[1]/ul/li[1]/a').get_attribute('href') # News link
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[3]').click() # click meny panel
        les_data[7] = count_students(les_data[3], les_data[2])
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[3]').click() # click meny panel
    if les_data[2] > 1:
        for les_data1 in report_data:
            if les_data[3] == les_data1[3] and les_data1[9] == '':
                les_data1[7] = les_data[7]
                les_data1[9] = les_data[9]

print('This day you have next lessons:')
for lesson in report_data:
    print(lesson)

#driver.get('https://sdo.rgsu.net/journal/laboratory/extended/lesson_id/382820/subject_id/45608') ## удалить строчку после отладки журнала посещений

# report_data[][7] - количество посещений - должен быть массив размером в количество пар с группой
# report_data[][2] - количество пар с этой группой - для отладки введу переменную:
#rd2 = 2


    

    



#f = open('rgsu.html', 'w')
#f.write(html)
#f.close()

#driver.quit()
print("Driver Turned Off")
