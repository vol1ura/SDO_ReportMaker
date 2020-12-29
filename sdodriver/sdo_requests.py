import requests


class Session:
    SDO_URL = 'https://sdo.rgsu.net'

    @staticmethod
    def get_headers(referer='https://sdo.rgsu.net/') -> dict:
        return {  # HTTP headers for sdo.rgsu.net
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': Session.SDO_URL,
            'Connection': 'keep-alive',
            'Referer': referer}

    def sdo_post(self, url: str, payload: dict):
        return self.sdo.post(url, data=payload, headers=Session.get_headers(url))

    def __init__(self, login, password):
        LOGIN_URL = 'https://sdo.rgsu.net/index/authorization/role/guest/mode/view/name/Authorization'
        payload = {
            "start_login": 1,
            "login": login,
            "password": password
        }
        self.sdo = requests.session()
        # Perform login
        result = self.sdo_post(LOGIN_URL, payload)
        if result.ok and ('Пользователь успешно авторизован.' in result.text):
            print('Login OK!')
        else:
            raise SystemExit('Login failed! Check settings.')
        # Tutor mode on
        result = self.sdo.get('https://sdo.rgsu.net/switch/role/tutor', headers=Session.get_headers())
        if result.ok:
            print('Tutor mode ON!')
        else:
            raise SystemExit('Tutor mode failed. Try again later.')

    def make_news(self, announce: str, message: str, subject_id: str):
        url = '/news/index/new/subject/subject/subject_id/' + subject_id
        payload = {'id': 0,
                   'cancelUrl': url,
                   'subject_name': 'subject',
                   'subject_id': subject_id,
                   'announce': announce,
                   'message': message,
                   'submit': 'Сохранить'
                   }
        self.sdo_post(Session.SDO_URL + url, payload)

    def grade_student(self, student_url, ball):
        grading = {  # Grading settings
            "interview_id": 0,  # always 0
            "type": 5,  # 3=Ответ преподавателя, 4=Требования на доработку, 5=Выставлена оценка
            "range_mark": 5 if ball > 84 else 4 if ball > 74 else 3 if ball > 64 else 2,  # оценка
            "ball": ball  # оценка в баллах 1-100
        }
        self.sdo_post(student_url, grading)

    def set_attendance(self, subject_id: str, lesson_id: str, date_id: str, j_type: int, date: str, user_ids: list):
        """
        Fill journal of students attendance
        """
        payload = {"journal_type": j_type, f"day_old_{date_id}": date}
        [payload.setdefault(f"isBe_user_{user_id}_{date_id}", 1) for user_id in user_ids]
        headers = Session.get_headers('https://sdo.rgsu.net/journal/laboratory/extended/lesson_id/' +
                                      lesson_id + '/subject_id/' + subject_id)
        url = 'https://sdo.rgsu.net/journal/storage/save/lesson_id/' + \
              lesson_id + '/subject_id/' + subject_id + '/referer_redirect/1'
        self.sdo.post(url, payload=payload, headers=headers)

    def make_topic(self, title, text, forum_url):
        payload = {'title': title, 'text': text}
        headers = Session.get_headers(forum_url)
        return self.sdo.post(forum_url + '/0/newtheme/create', data=payload, headers=headers)
