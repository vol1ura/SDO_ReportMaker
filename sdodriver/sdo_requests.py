import requests
from lxml.html import parse


class PortalRGSU:
    SDO_URL = 'https://sdo.rgsu.net'

    @staticmethod
    def get_headers(referer='https://sdo.rgsu.net/') -> dict:
        return {  # HTTP headers for sdo.rgsu.net
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0',
            'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': PortalRGSU.SDO_URL,
            'Connection': 'keep-alive',
            'Referer': referer}

    def __init__(self, login: str, password: str):
        login_url = 'https://sdo.rgsu.net/index/authorization/role/guest/mode/view/name/Authorization'
        payload = {
            "start_login": 1,
            "login": login,
            "password": password
        }
        self.sdo = requests.session()
        # Perform login
        result = self.sdo_post(login_url, payload)
        if result.ok and ('Пользователь успешно авторизован.' in result.text):
            print('Login OK!')
        else:
            raise SystemExit('Login failed! Check settings.')
        # Tutor mode on
        result = self.sdo.get('https://sdo.rgsu.net/switch/role/tutor', headers=PortalRGSU.get_headers())
        if result.ok:
            print('Tutor mode ON!')
        else:
            raise SystemExit('Tutor mode failed. Try again later.')

    def sdo_post(self, url: str, payload: dict, action='', stream=False):
        return self.sdo.post(url + action, data=payload, headers=PortalRGSU.get_headers(url), stream=stream)

    def make_news(self, announce: str, message: str, subject_id: str) -> str:
        """Creating news in the course (sdo.rgsu.net -> Services -> News).

        :param announce: title of news
        :param message: body of news
        :param subject_id: course id as string
        :return: url of created news record
        """
        url = '/news/index/new/subject/subject/subject_id/' + subject_id
        payload = {'id': 0,
                   'cancelUrl': url,
                   'subject_name': 'subject',
                   'subject_id': subject_id,
                   'announce': announce,
                   'message': message,
                   'submit': 'Сохранить'
                   }
        result = self.sdo_post(PortalRGSU.SDO_URL + url, payload)
        result = self.sdo.get(result.url.replace('/ajax/true', ''), stream=True)
        result.raw.decode_content = True
        tree = parse(result.raw)
        created_news_link = tree.xpath('//div[@class="news-title"]/a/@href')[0]
        return PortalRGSU.SDO_URL + created_news_link

    def grade_student(self, student_url, ball):
        grading = {  # Grading settings
            "interview_id": 0,  # always 0
            "type": 5,  # 3=Ответ преподавателя, 4=Требования на доработку, 5=Выставлена оценка
            "range_mark": 5 if ball > 84 else 4 if ball > 74 else 3 if ball > 64 else 2,  # оценка
            "ball": ball  # оценка в баллах 1-100
        }
        self.sdo_post(student_url, grading)

    def set_attendance(self, action_url: str, date_id: str, j_type: int, date: str, lesson_online: bool, user_ids):
        """Fill journal of students attendance

        :param action_url: relative url to post action of the journal
        :param date_id: id of column in journal
        :param j_type: integer internal identifier of journal
        :param date: string in format DD.MM.YYYY it will be written in column head
        :param lesson_online: True if lesson in online format, False if offline
        :param user_ids: list or set of id of students to set attendance in journal
        :return: Response
        """
        payload = {"journal_type": j_type, f"day_old_{date_id}": date}
        [payload.setdefault(f"isBe_user_{user_id}_{date_id}", 1) for user_id in user_ids]
        if lesson_online:
            [payload.setdefault(f"format_attendance_user_{user_id}_{date_id}", 2) for user_id in user_ids]  # online = 2
        return self.sdo_post(self.SDO_URL, action=action_url, payload=payload)

    def make_topic(self, title: str, text: str, subject_id: str):
        """Creating new forum topic in the course (sdo.rgsu.net -> Services -> Forum).

        :param title: title of forum topic
        :param text: body of forum topic
        :param subject_id: course id as string
        :return: request response
        """
        payload = {'title': title, 'text': text}
        url = PortalRGSU.SDO_URL + '/forum/subject/subject/' + subject_id
        return self.sdo_post(url, action='/0/newtheme/create', payload=payload)

    def make_report(self, timetable_id: int, n: int, video_link: str, news_link: str) -> bool:
        """Making report record about lesson

        :param timetable_id: integer identifier of report table
        :param n: number of students on the lesson
        :param video_link: url to shared video
        :param news_link: url to news topic
        :return: True if adding of report record was successful and False if failed
        """
        url = 'https://sdo.rgsu.net/timetable/teacher'
        payload = {"timetable_id": timetable_id,
                   "users": n,
                   "file_path": video_link,
                   "subject_path": news_link}
        response = self.sdo_post(url, action='/save-additional', payload=payload)
        if response.json().get('message') == "Сохранено":
            return True
        else:
            return False


# TODO: make separate class Timetable and implement this function as a private method
def get_table_id(portal: PortalRGSU, lessons: list):
    WEEKDAYS = {'Понедельник': 1, 'Вторник': 2, 'Среда': 3, 'Четверг': 4, 'Пятница': 5, 'Суббота': 6}
    timetable_link = 'https://sdo.rgsu.net/timetable/teacher'
    result = portal.sdo.get(timetable_link, stream=True)
    result.raw.decode_content = True
    tree = parse(result.raw)
    rows = tree.xpath('//tr[@class="tt-row"]')
    for lesson in lessons:
        for row in rows:
            # Read lines, parse weekday, time and group
            cells = row.xpath('.//td/text()')
            if lesson['time'].isoweekday() == WEEKDAYS[cells[6].strip()] and \
                    lesson['time'].hour == int(cells[0].strip()[:2]) and \
                    lesson['time'].minute == int(cells[0].strip()[3:5]) and \
                    lesson['group'] == cells[3].strip():
                lesson['timetable_id'] = int(row.xpath('.//td[9]/button/@data-timetable_id')[0])
    return lessons
