from msedge.selenium_tools import Edge, EdgeOptions  # pip install msedge-selenium-tools
# If you are able to upgrade to Selenium 4 Alpha, there is no need to use this package as
# Selenium should already have everything you need built in! pip install selenium==4.0.0.a7
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep


class Driver(Edge):   # for Edge browser
    def __init__(self, browser, driver_path):
        # Read this first https://docs.microsoft.com/en-us/microsoft-edge/webdriver-chromium/?tabs=python
        # Download https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
        # https://pypi.org/project/msedge-selenium-tools/
        edge_options = EdgeOptions()
        edge_options.use_chromium = True  # if we miss this line, we can't make Edge headless
        # A little different from Chrome cause we don't need two lines before 'headless' and 'disable-gpu'
        edge_options.add_argument('headless')
        edge_options.add_argument('disable-gpu')
        Edge.__init__(self, options=edge_options, executable_path=driver_path)
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
