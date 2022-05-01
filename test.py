import base64
import json
import os
import time

import ddddocr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager


def get_captcha():
    img_base64 = CHROME.execute_script("""
        var ele = arguments[0];
        var cnv = document.createElement('canvas');
        cnv.width = ele.width; cnv.height = ele.height;
        cnv.getContext('2d').drawImage(ele, 0, 0);
        return cnv.toDataURL('image/jpeg').substring(22);    
        """, CHROME.find_element_by_xpath('''//*[@id="ChkImg"]'''))

    with open("captcha_login.png", 'wb') as image:
        image.write(base64.b64decode(img_base64))
    ocr = ddddocr.DdddOcr()
    with open('captcha_login.png', 'rb') as f:
        img_bytes = f.read()
    captcha = ocr.classification(img_bytes) # 驗證碼
    return captcha


def login():
    CHROME.find_element_by_id("USERNAME").send_keys(MAIL)
    CHROME.find_element_by_id("PASSWORD").send_keys(PASSWORD)
    CHROME.find_element_by_id("UserInputNo").send_keys(get_captcha())
    CHROME.find_element_by_name("LOGIN").click()
    time.sleep(1)

    alert_text = CHROME.switch_to.alert.text
    alert = CHROME.switch_to.alert
    alert.accept()

    if "驗證碼" in alert_text:
        time.sleep(1)
        login()


def select_venues_in_Taipei_Gymnasium7F():
    SELECT = Select(CHROME.find_element_by_id('RentalData'))
    DATEBOX = {}

    for time_choose in SELECT.options: # 選時間
        print(time_choose.text)        # 印出日期
        SELECT.select_by_value(time_choose.text)
        time.sleep(1)
        for venu_num in range(727, 737): # 選場地
            venue = f"SubVenues_{venu_num}"
            CHROME.find_element_by_id(venue).click()
            time.sleep(1.5)

            time_interval = CHROME.find_elements_by_class_name("BookB.UnBooked")
            if len(time_interval) == 0:
                continue

            DATEBOX[time_choose.text] = {}
            DATEBOX[time_choose.text][venue] = []
            for times in time_interval:
                DATEBOX[time_choose.text][venue].append(times.text)
            
            time.sleep(1)

    print(json.dumps(DATEBOX, indent=2))
    # for times in time_interval:
    #     print(times.text)


def input_Participate():
    CHROME.find_element_by_id("ParticipateTypeG").send_keys(GENERAL_STATUS)
    CHROME.find_element_by_id("ParticipateTypeP").send_keys(PREFERENTIAL_STATUS)


def send():
    CHROME.find_element_by_name("Send").click()

if __name__ == '__main__':
    MAIL = "showder2@hotmail.com"
    PASSWORD = "1qazXSW@"

    LOGIN_URL = r"https://sports.tms.gov.tw/member/?BURL=%2Forder_rental%2F%3FU%3Dvenue%26K%3D49"
    GENERAL_STATUS = '2' # 一般身分人數
    PREFERENTIAL_STATUS = '3' # 優待身分人數

    OPTIONS = Options()
    OPTIONS.add_argument("--disable-notifications")
    OPTIONS.add_argument("--start-maximized")
    PWD = os.path.dirname(__file__)


    try:
        CHROME = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=OPTIONS)
        CHROME.get(LOGIN_URL)
        time.sleep(3)

        login()
        time.sleep(3)

        select_venues_in_Taipei_Gymnasium7F()
        # input_Participate()
        # send()
        time.sleep(3)
    except Exception as e:
        print("Error:", e)
    finally:
        CHROME.quit()
