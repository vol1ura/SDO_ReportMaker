from infoout import mymes, get_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import sys

# if __name__ == '__name__':
login, password, _, _, browser, browser_driver_path = map(str.strip, get_settings('settings.txt'))


def sdodriver():
    if browser[0] == 'F':
        from selenium.webdriver.firefox.options import Options  # for Firefox browser
    elif browser[0] == 'C' or browser[0] == 'G':
        from selenium.webdriver.chrome.options import Options  # for Chrome browser

    opts = Options()
    # opts.add_argument("--headless")
    opts.add_argument('--ignore-certificate-errors')
    mymes('Driver is starting now', 0, False)
    mymes("Please wait, don't close windows!", 0, False)

    # =============================================================================
    # Browser driver initialization
    # =============================================================================
    if browser[0] == 'F':
        # Download driver on https://github.com/mozilla/geckodriver/releases
        driver = webdriver.Firefox(options=opts, executable_path=browser_driver_path)
    elif browser[0] == 'C' or browser[0] == 'G':
        # Download Chrome driver if you use Google Chrome
        # https://sites.google.com/a/chromium.org/chromedriver/home
        driver = webdriver.Chrome(chrome_options=opts, executable_path=browser_driver_path)
    else:
        sys.exit('Error! Unknown name of browser. Please check requirements ans file settings.txt')

    # driver = webdriver.Safari(executable_path = r'/usr/bin/safaridriver') # for MacOS

    wait = WebDriverWait(driver, 20)
    mymes('Headless Mode is initialized', 0)

    # =============================================================================
    # Login on sdo.rgsu.net
    # =============================================================================
    driver.get('https://sdo.rgsu.net/')
    get_link = wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'login')))
    get_link.click()
    mymes('Opening login form', 1, False)
    mymes('Entering login and password', 1, False)
    driver.find_element_by_id('login').send_keys(login)
    driver.find_element_by_id('password').send_keys(password)
    # Submit authorization:
    get_link = wait.until(ec.element_to_be_clickable((By.ID, 'submit')))
    get_link.click()
    # Tutor mode ON:
    get_link = wait.until(ec.element_to_be_clickable((By.XPATH, '//div[@class="hm-roleswitcher"]/div[2]')))
    get_link.click()

    driver.maximize_window()
    return driver
