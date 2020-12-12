from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from webdav3.client import Client


class FFDriver(webdriver.Firefox):
    def __init__(self, driver_path):
        from selenium.webdriver.firefox.options import Options  # for Firefox browser
        # webdriver.Safari(executable_path = r'/usr/bin/safaridriver') # for MacOS
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--ignore-certificate-errors')
        webdriver.Firefox.__init__(self, options=opts, executable_path=driver_path)


class GCDriver(webdriver.Chrome):
    def __init__(self, driver_path):
        from selenium.webdriver.chrome.options import Options  # for Chrome browser
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--ignore-certificate-errors')
        webdriver.Chrome.__init__(self, options=opts, executable_path=driver_path)


class Driver(FFDriver, GCDriver):
    def __init__(self, browser, driver_path):
        if browser[0] == 'F':
            FFDriver.__init__(self, driver_path)
        elif browser[0] == 'G' or browser[0] == 'C':
            GCDriver.__init__(self, driver_path)
        self.implicitly_wait(5)  # seconds - use carefully!
        self.wait = WebDriverWait(self, 20)
        self.maximize_window()

    def open_sdo(self, login, password):
        self.get('https://sdo.rgsu.net/')
        element = self.wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'login')))
        element.click()
        sleep(1)
        self.find_element_by_id('login').send_keys(login)
        self.find_element_by_id('password').send_keys(password)
        element = self.wait.until(ec.element_to_be_clickable((By.ID, 'submit')))  # submit authorization
        element.click()
        sleep(1)
        # tutor mode ON:
        element = self.wait.until(ec.element_to_be_clickable((By.XPATH, '//div[@class="hm-roleswitcher"]/div[2]')))
        element.click()

    def open_cloud(self, login, password):
        self.get('https://cloud.rgsu.net/')
        sleep(1)
        self.find_element_by_id('user').send_keys(login)
        self.find_element_by_id('password').send_keys(password)
        self.find_element_by_id('submit-form').click()

    def scroll_page(self, web_element, t=2.0):
        self.execute_script('arguments[0].scrollIntoView({block: "center", inline: "center"})', web_element)
        sleep(t)

    def turnoff(self):
        self.quit()
        print('Driver Turned Off')


class CloudDriver(Client):  # using webdav protocol for fast getting information and creating paths
    def __init__(self, login, password, token):
        opts = {
            'webdav_hostname': token,
            'webdav_login': login,
            'webdav_password': password,
        }
        Client.__init__(self, opts)

    def free_space(self):
        fs = float(self.free())
        for i in range(3):
            fs /= 1024
        color = '\033[31m' if fs < 10 else '\033[32m'
        print(f'Free space in your cloud [cloud.rgsu.net]: {color}{fs:.1f}\033[0m GB')

    def check_path(self, p_dir: str):
        if not self.check(p_dir):
            self.mkdir(p_dir)
            print(f'Directory [\033[36m{p_dir}\033[0m] created.')
