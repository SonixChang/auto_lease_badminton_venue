import base64
import json
import os
import time
import sys

import ddddocr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

from datetime import timedelta
import schedule

def job():  
    os.system(r"start scheduler.bat")

def get_captcha():
    img_base64 = CHROME.execute_script("""
        var ele = arguments[0];
        var cnv = document.createElement('canvas');
        cnv.width = ele.width; cnv.height = ele.height;
        cnv.getContext('2d').drawImage(ele, 0, 0);
        return cnv.toDataURL('image/jpeg').substring(22);    
        """, CHROME.find_element_by_xpath('''//*[@id="ChkImg"]'''))

    with open(PWD + ".\captcha_login.png", 'wb') as image:
        image.write(base64.b64decode(img_base64))
    ocr = ddddocr.DdddOcr(show_ad=False, import_onnx_path=PWD + '\common.onnx')
    with open(PWD + '.\captcha_login.png', 'rb') as f:
        img_bytes = f.read()
    captcha = ocr.classification(img_bytes) # 驗證碼
    os.remove(PWD + '.\captcha_login.png')
    return captcha

def login():
    for _ in range(3):
        CHROME.find_element_by_id("USERNAME").send_keys(MAIL)
        CHROME.find_element_by_id("PASSWORD").send_keys(PASSWORD)
        CHROME.find_element_by_id("UserInputNo").send_keys(get_captcha())
        CHROME.find_element_by_name("LOGIN").click()
        time.sleep(1)

        alert_text = CHROME.switch_to.alert.text
        alert = CHROME.switch_to.alert
        alert.accept()

        if "登入完成" in alert_text:
            time.sleep(1)
            return
    raise Exception("登入失敗!!!")

def find_consecutive_and_choose(date_choose):
    DATE = Select(CHROME.find_element_by_id('RentalData'))
    DATE_LIST = []

    for date_item in DATE.options:
        DATE_LIST.append(date_item.text)

    if date_choose in DATE_LIST:
        return True

    return False

def check_date():
    global lease_situation
    global CHROME
    try:
        CHROME = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=OPTIONS)
        CHROME.get(LOGIN_URL)
        time.sleep(3)
        login()
        time.sleep(1.5)


        lease_situation = find_consecutive_and_choose(LEASE_DATE)
        print(lease_situation)
        CHROME.close()
    except:
        try:
            CHROME.close()
        except:
            pass


if __name__ == "__main__":
    PWD = os.path.dirname(os.path.realpath(sys.executable))
    with open(PWD + '\check_date.json', 'r', encoding='utf-8') as f:
        InputData = json.load(f)

    LOGIN_URL = InputData['login_url']
    MAIL = InputData['mail']
    PASSWORD = InputData['password']
    LEASE_DATE = InputData['lease_date']

    OPTIONS = Options()
    OPTIONS.add_argument("--start-maximized")
    OPTIONS.add_argument("--disable-notifications")
    lease_situation = False

    schedule.every(1).minute.until(timedelta(minutes=30)).do(check_date)
    
    while lease_situation == False:
        schedule.run_pending()
    if lease_situation == True:
        schedule.clear()
        job()