# ReportMaker - автоматическое создание отчёта преподавателя
Скрипт обрабатывает данные в личном кабинете преподавателя на сайте sdo.rgsu.net, создаёт новости в соответствующих курсах (согласно требованиям) и заполняет отчёт о проведённых занятиях в заданную дату.

## Как пользоваться?
1. *Скачать скрипт* `ReportMaker.py` в какой-нибудь каталог на компьютере
2. *Скачать драйвер* своего браузера (см. ниже)
3. *Заполняем журналы* посещения занятий (важно изначально последовательно заполнять столбцы журнала)
4. *Видеозаписи* проведённых занятий должны именоваться последовательно Video1 Video2 ... Video6. Желательно, чтобы они находились в отдельной папке на диске
5. *Cоздать текстовый файл* `settings.txt` в каталоге скрипта (см. ниже). Создаётся один раз, затем меняем там только дату
6. *Запускаем скрипт* либо из командной строки `python ReportMaker.py`, либо кликая `ReportMaker.bat`. Если отчёт заполняется за другой день, надо передать дату через командную строку `python ReportMaker.py дд.мм.гг` или `ReportMaker.bat дд.мм.гг` (заполнить можно только отчёты текущей недели)
7. Идём *пить чай*

## Что получаем?
* Новости для всех групп и курсов из расписания на заданную дату

![News](/pics/screenshot1.png)

* Заполненный отчёт по заданной дате

![Report](/pics/screenshot3.png)

* Видеоматериалы загружены в облако РГСУ

* Файл report.txt в том же каталоге c результатами работы скрипта - пары, группы, количество посещений, ссылка на новость, ссылка на видеоматериал.

## Формат файла settings.txt
Создаём простой текстовый файл, состоящий из 6 строк: 
1. Ваш *логин* для [sdo.rgsu.net](https://sdo.rgsu.net)
2. Ваш *пароль* для [sdo.rgsu.net](https://sdo.rgsu.net)
3. *URL-токен* для доступа к [cloud.rgsu.net](https://cloud.rgsu.net) по протоколу WebDAV
4. *Путь к каталогу с видеозаписями* проведённых в этот день занятий. Число видео = числу пар в этот день! Файлы должны называться **строго** Video1, Video2 и т.д.
5. *Название вашего браузера* - Firefox или Google Chrome. Под Safari скрипт нужно поправить вручную.
6. *Путь к драйверу* вашего браузера (можно поместить его, например, в том же каталоге - см. пример)

Если где-то, например, в пути к видеофайлам используется кириллица, файл должен быть сохранён **строго** в кодировке UTF-8! Желательно, чтобы пути были без кириллицы и без пробелов.

Например,
> volodinyv<br />
> qWerTy<br />
> https://cloud.rgsu.net/remote.php/dav/files/AAA1BBBC-1234-5678-9DEF-AA00000000BC/<br />
> C:\\Users\\Yuriy\\Downloads\\rgsu_video<br />
> Firefox<br />
> .\\geckodriver.exe

URL-токен копируется из личного кабинета [cloud.rgsu.net](https://cloud.rgsu.net). Это делается единожды. По сути, в настройках далее больше ничего менять не придётся, **отчёты будут заполняться одним кликом мышкой**

![WebDAV-token](/pics/screenshot4.png)

## Особенности и возможные проблемы
Скрипт работает относительно неторопливо, так как страницы sdo.rgsu.net грузятся медленно. 
Порой sdo.rgsu.net начинает очень сильно тормозить и тогда скрипт может вылетать с ошибкой, так как выставленные тайминги закончились, а нужный элемент на страничке всё ещё не прогрузился. Тем более это возможно, если у вас нестабильный интернет. 
Можно попровать в соответствующих местах скрипта увеличить задержки или дополнительно вставить там команду `sleep(10)`.

Ещё одна особенность - это требование *соблюдения последовательности* при заполнении журналов посещаемости. Рекомендую при заполнении сразу переходить в режим отображения всех столбцов. Если вы заполняли стобцы журнала не последовательно от первого занятия в крайнем левом столбце к крайнему правому столцу для последней пары в семестре, скрипт скрорее всего, вычислит что-то ещё, но количество присутствующих в заданную дату, придётся вручную скорректировать значение в отчёте.

## Системные требования
* Python версии не ниже 3.4, а лучше не ниже 3.7.
* Установлен пакет selenium для Python - `pip3 install selenium`. Желательно последней версии (я тестировал с версией 3.141.0).
* Установлен пакет webdav3 для Python - `pip3 install webdavclient3`.
* Скрипт протестирован с браузером Firefox v83.0 (64-битный). Сообщалось, что с Chrome тоже работает.
* Скрипт протестирован с драйвером браузера geckodriver v0.28.0 (win64). Сообщалось, что chromedriver 32bit тоже работает.
* Стабильное скоростное подключение к Internet (20 Mbit/s и выше).
* Оперативная память от 2 Gb.
* Разрешение экрана не менее FullHD (1920×1080 pixels).

## Драйвер браузера
Если вы используете Firefox, то скачиваете `geckodriver.exe`, а если Chrome, то `chromedriver.exe`. В `settings.txt` прописываем название браузера, скрипт автоматически определяет какой драйвер использовать и какие модули загружать.
 
Ссылки для загрузки драйвера
1. geckodriver доступен здесь https://github.com/mozilla/geckodriver/releases
2. chromedriver доступен здесь https://sites.google.com/a/chromium.org/chromedriver/home

## Работа скрипта
Запускается скрипт из командной строки 
```bash
python3 ReportMaker.py [date]
```
или из вашего любимого IDE. Параметр date необязательный. Если он не указан, то отчёт формируется для текущего дня. Если указываете дату, то она должна принадлежать текущей рабочей неделе и должна быть в формате ДД.ММ.ГГ либо ДД.ММ.ГГГГ

Скорее всего, предварительно потребуется установить пакеты `selenium` и `webdav3`:
```bash
pip3 install selenium, webdavclient3
```
или 
```bash
python3 -m pip install selenium, webdavclient3
```

![Script is working](/pics/screenshot2.png)

### Что добавлено?

Версия 1.1:
* По умолчанию используется текущая дата. Файл настроек теперь нужно править каждый раз. Альтернативная дата передаётся через параметр командной строки
* Теперь можно использовать любой формат даты - как ДД.ММ.ГГГГ, так и ДД.ММ.ГГ
* Небольшая оптимизация

Версия 1.0:
* Добавлена автоматическая загрузка видео в [cloud.rgsu.net](https://cloud.rgsu.net) по протоколу WevDAV
* Автоматическая генерация ссылок на видеоматериалы в [cloud.rgsu.net](https://cloud.rgsu.net)
* Оптимизированы задержки и ускорена работа
* Повышена стабильность
* Локаторы элементов изменены на более универсальные
* Добавлен файл `ReportMaker.bat` для запуска скрипта сразу из проводника Windows (рекомендуется)
* Хранение всех настроек в одном файле

Версия 0.92a:
* Хранение логина и пароля от аккаунта [sdo.rgsu.net](https://sdo.rgsu.net) вынесено во внешний каталог в отдельный файл

Hotfix 0.91:
* Пофикшена проверка группы в списке Мои курсы. У некотрых групп набор параметров отличается. Теперь должно работать в широких пределах
* Пофикшен запрос получения ссылки на новость, который поломался после добавления разработчиками сайта новой кнопочки на страничку Новости

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
- [ ] Асинхронная передача видео c выводом прогресса
- [ ] Проверить возможность многопоточной загрузки
- [ ] Перехват и отправка запросов с помощью модуля Requests
- [ ] Переделать выбор дат в журнале посещения, так как некоторые преподаватели заполняют журнал непоследовательно 
(практически нереально реализовать так, чтобы учесть все варианты, тут сказываются также ососенности составления расписания в РГСУ и самой СДО). 
Всё решит только автоматическое заполнение журнала посещаемости через Goggle Формы
- [x] Автоматическая загрузка видео в cloud
- [ ] Автоматическае отметка студентов в журнале посещений. Реализация через Google Формы и Google Таблицы
- [ ] Протестировать и отладить работу с chromedriver
- [x] Оптимизировать задержки
- [ ] Переделать структуру данных из массива в словарь
- [ ] Время можно хранить в одной ячейке
 