from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep


class FFDriver(webdriver.Firefox):
    def __init__(self, driver_path):
        from selenium.webdriver.firefox.options import Options  # for Firefox browser
        # webdriver.Safari(executable_path = r'/usr/bin/safaridriver') # for MacOS
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--ignore-certificate-errors')
        super().__init__(options=opts, executable_path=driver_path)


class GCDriver(webdriver.Chrome):
    def __init__(self, driver_path):
        from selenium.webdriver.chrome.options import Options  # for Chrome browser
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--ignore-certificate-errors')
        super().__init__(chrome_options=opts, executable_path=driver_path)


class SDriver(webdriver.Safari):  # for MacOS Safari
    def __init__(self, driver_path=r'/usr/bin/safaridriver'):
        # See https://webkit.org/blog/6900/webdriver-support-in-safari-10/
        super().__init__(executable_path=driver_path)


class Driver(FFDriver, GCDriver, SDriver):
    def __init__(self, browser='F', driver_path='./geckodriver.exe'):
        if browser[0] == 'F':
            FFDriver.__init__(self, driver_path)
        elif browser[0] == 'G' or browser[0] == 'C':
            GCDriver.__init__(self, driver_path)
        elif browser[0] == 'S':
            SDriver.__init__(self, driver_path)
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