# ReportMaker - автоматическое создание отчёта преподавателя
Скрипт обрабатывает данные в личном кабинете преподавателя на сайте sdo.rgsu.net, создаёт новости в соответствующих курсах (согласно требованиям) и заполняет отчёт о проведённых занятиях в заданную дату.

## Как пользоваться?
1. *Скачать скрипт* `ReportMaker.py` в какой-нибудь каталог на компьютере.
2. В том же каталоге *должен лежать драйвер* браузера (см. ниже) - например, `geckodriver.exe`.
3. *Заполняем журналы* посещения занятий
4. *Загружаем видеозаписи* проведённых занятий в облако (скрипт пока не умеет этого делать)
5. В каталоге скрипта *создать файл* `settings.txt` (см. ниже)
6. *Запускаем скрипт* `python ReportMaker.py`
7. Идём *пить чай*

## Что получаем?
* Новости для всех групп и курсов из расписания на заданную дату

![News](/pics/screenshot1.png)

* Заполненный отчёт по заданной дате

![Report](/pics/screenshot3.png)

* Файл report.txt в том же каталоге c результатами работы скрипта - пары, группы, количество посещений, ссылка на новость, ссылка на видеоматериал.

## Формат файла settings.txt
Создаём простой текстовый файл 
1. В первой строчке указывается дата, по которой должен заполняться отчёт, строго ДД.ММ.ГГГГ
2. Во второй строчке - ваш *логин* для sdo.rgsu.net
3. В третьей строчке - ваш *пароль* для sdo.rgsu.net
4. В четвертой строчке что угодно, она не ипользуется, просто разделитель
5. Пятая и последующие строки содержат *ссылки* из cloud.rgsu.net на загруженные записи трансляций пар в том порядке и том количестве, 
как они идут в **Расписании занятий** на sdo.rgsu.net для **заданной даты**
Пока скрипт не умеет автоматически загружать видео

Например,
> 18.11.2020<br />
> volodinyv<br />
> qwerty<br />
> ########################################<br />
> https://cloud.rgsu.net/s/перваяпарасгруппой1<br />
> https://cloud.rgsu.net/s/втораяпарасгруппой1<br />
> https://cloud.rgsu.net/s/третьсяпарасгруппой2<br />
> https://cloud.rgsu.net/s/третьяпарасгруппой3<br />
> https://cloud.rgsu.net/s/четвертаяпарасгруппой4<br />
> https://cloud.rgsu.net/s/четвертаяпарасгруппой4<br />

## Особенности и возможные проблемы
Скрипт работает весьма неторопливо, так как страницы sdo.rgsu.net грузятся медленно. 
Порой сайт начинает очень сильно тормозить и тогда скрипт будет вылетать с ошибкой, так как выставленные тайминги закончились, а нужный элемент на страничке всё ещё не прогрузился. 
Тем более это возможно, если у вас нестабильный интернет. 
Можно попровать в соответствующих местах скрипта увеличить задержки или дополнительно вставить там команду `sleep(10)`.

К тому же selenium - капризный пакет, требующий множества проверок и тестирования. Возможно, придётся ещё поотлаживать работу скрипта.

## Системные требования
* Python версии не ниже 3.4, рекомендуется версия 3.8.
* Установлен пакет Selenium для Python - `pip3 install selenium`. Желательно последней версии (я тестировал с версией 3.141.0)
* Скрипт протестирован с браузером Firefox v82.0.2 (64-битный). Работа с Chrome в системе не проверялась.
* Скрипт протестирован с драйвером браузера geckodriver v0.28.0 (win64). Работа с chromedriver не проверялась.
* Стабильное скоростное подключение к Inretnet (20 Mbit/s и выше)
* Оперативная память от 2 Gb
* Разрешение экрана не менее FullHD (1920×1080 pixels)

## Драйвер браузера
 Т.к. я пользуюсь Firefox, то скрипт настроен на работу с `geckodriver.exe`. 
 Но вы можете перенастроить под Chrome и использовать `chromedriver.exe`, достаточно раскомментировать нужные строчки скрипта и закомментировать ненужные.
 
Ссылки для загрузки драйвера
1. geckodriver доступен здесь https://github.com/mozilla/geckodriver/releases
2. chromedriver доступен здесь https://sites.google.com/a/chromium.org/chromedriver/home

## Работа скрипта
Запускается скрипт из командной строки 
```bash
python3 ReportMaker.py
```
или из вашего любимого IDE. 

Скорее всего, предварительно потребуется установить пакет selenium 
```bash
pip3 install selenium
```
или 
```bash
python3 -m pip install selenium
```

![Script is working](/pics/screenshot2.png)

### Что добавлено?
Версия 0.9:
* Заполняется отчёт в расписании преподавателя
* Некоторые улучшения и оптимизация скорости работы

Версия 0.8:
* Подсчитывается посещаемость
* Заполняются новости и создаётся файл report.txt с ссылками на них

Версия 0.7:
* Убрал использование пакета BeautifulSoup, оставил только Selenium
* Скрипт заходит в расписание и обрабатывает данные по заданному дню 

### ToDo
- [ ] Автоматическая загрузка видео в cloud.
- [ ] Автоматическае отметка студентов в журнале посещений. Реализация через Google Формы и Google Таблицы.
- [ ] Протестировать и отладить работу с chromedriver
- [ ] Оптимизировать задержки
- [ ] Переделать структуру данных из массива в словарь
- [ ] Время можно хранить в одной ячейке
 
