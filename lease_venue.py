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
    ocr = ddddocr.DdddOcr(show_ad=False, import_onnx_path = LAST_PWD + '\common.onnx')
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


def find_consecutive_and_choose(date_choose: str, ini_court: int, fin_court: int, specify_ini_time: int, specify_fin_time: int):
    global LEASE_TOTAL_TIME
    DATE = Select(CHROME.find_element_by_id('RentalData'))
    DATE_LIST = []
    lease_situation = False
    VENUE = {}
    
    TwoHours = True
    if LEASE_TOTAL_TIME == 3:
        TwoHours = False

    for venu_num in range(ini_court, fin_court + 1): # 建立場地dict
        venu_num += 726
        venue_id = f"SubVenues_{venu_num}"
        venu_num -= 726
        VENUE[venue_id] = f"Court {venu_num}"

    for date_item in DATE.options:
        DATE_LIST.append(date_item.text)

    if date_choose in DATE_LIST:
        DATE.select_by_index(0) # 校正     
        DATE.select_by_value(date_choose) # 
        time.sleep(1)

        for venu_num in range(ini_court, fin_court + 1): # 選場地
            venu_num += 726
            venue_id = f"SubVenues_{venu_num}"
            CHROME.find_element_by_id(venue_id).click()
            time.sleep(1.5)

            time_interval = CHROME.find_elements_by_class_name("BookB.UnBooked")
            if TwoHours:
                if len(time_interval) < 2:
                    continue
                for times in time_interval:  # 租2hrs
                    if specify_ini_time <= int(times.text[:2]) < specify_fin_time - 1: # 指定起始時間
                        cure_fin_time = times.text[-5:]
                        next_ini_time = time_interval[time_interval.index(times)+1].text[:5]
                        if cure_fin_time == next_ini_time:    # 判斷是否連續

                            times.click()
                            time_interval[time_interval.index(times)+1].click()
                            
                            if VENUE[venue_id] not in VenueAndTimeYouLease:
                                VenueAndTimeYouLease[VENUE[venue_id]] = []
                            VenueAndTimeYouLease[VENUE[venue_id]].append(times.text)
                            VenueAndTimeYouLease[VENUE[venue_id]].append(time_interval[time_interval.index(times)+1].text)
                            print(VenueAndTimeYouLease)
                            LEASE_TOTAL_TIME += 2
                            lease_situation = True
                            return lease_situation                       # 有租到就終止副程式
        
        TwoHours = False
        for venu_num in range(ini_court, fin_court + 1): # 選場地
            venu_num += 726
            venue_id = f"SubVenues_{venu_num}"
            CHROME.find_element_by_id(venue_id).click()
            time.sleep(1.5)

            time_interval = CHROME.find_elements_by_class_name("BookB.UnBooked")
            
            if TwoHours == False:
                for times in time_interval:  # 租1hr
                    if specify_ini_time <= int(times.text[:2]) < specify_fin_time:# specify_ini_time <= time區間的初始時間 < specify_fin_time
                        times.click()
                        if VENUE[venue_id] not in VenueAndTimeYouLease:
                            VenueAndTimeYouLease[VENUE[venue_id]] = []
                        VenueAndTimeYouLease[VENUE[venue_id]].append(times.text)
                        print(VenueAndTimeYouLease)
                        LEASE_TOTAL_TIME += 1
                        lease_situation = True
                        if LEASE_TOTAL_TIME == 4:
                            return lease_situation
                if lease_situation == True:
                    return lease_situation
    else:
        raise Exception("Date not open yet.")
    return lease_situation


def input_Participate():
    CHROME.find_element_by_id("ParticipateTypeG").send_keys(GENERAL_STATUS)
    CHROME.find_element_by_id("ParticipateTypeP").send_keys(PREFERENTIAL_STATUS)


def send():
    CHROME.find_element_by_name("Send").click()
    time.sleep(1)
    CHROME.find_element_by_name("Send").click()
    time.sleep(2)


def create_lease():
    CHROME.find_element_by_id("Agree").click()
        # CHROME.find_element_by_class_name("Btn.Send").click()
        # time.sleep(0.5)
        # CHROME.find_element_by_name("Send").click()
    time.sleep(2)


def go_back_to_lease_page():
    CHROME.find_element_by_xpath('//*[@id="TMRight"]/div[2]/ul/li[3]/a/div').click()
    time.sleep(2)
    CHROME.find_element_by_xpath('//*[@id="MainContent"]/div[2]/div[1]').click()
    time.sleep(1)
    windows = CHROME.window_handles
    CHROME.switch_to.window(windows[-1])
    CHROME.find_element_by_xpath('//*[@id="SubMenu"]/div/a/span[1]').click()
    CHROME.find_element_by_xpath('//*[@id="RentMenu"]/table/tbody/tr/td[2]/a').click()
    time.sleep(1)



if __name__ == '__main__':
    PWD = os.path.dirname(os.path.realpath(sys.executable))
    LAST_PWD = os.path.dirname(PWD)
    with open(PWD + '\input.json', 'r', encoding='utf-8') as f:
        InputData = json.load(f)
    with open(LAST_PWD + '\check_date.json', 'r', encoding='utf-8') as f:
        Check_date = json.load(f)

    LOGIN_URL = InputData['login_url']
    MAIL = InputData['mail']
    PASSWORD = InputData['password']
    
    LEASE_DATE = Check_date['lease_date']
    INI_COURT = InputData['ini_court']
    FIN_COURT = InputData['fin_court']
    INI_TIME = InputData['ini_time']
    FIN_TIME = InputData['fin_time']
    GENERAL_STATUS = InputData['general_status'] # 一般身分人數
    PREFERENTIAL_STATUS = InputData['preferential_status'] # 優待身分人數
    
    VenueAndTimeYouLease = {}
    LEASE_TOTAL_TIME = 0    # 最長時間4hr

    OPTIONS = Options()
    # OPTIONS.add_argument("--headless")
    OPTIONS.add_argument("--start-maximized")
    OPTIONS.add_argument("--disable-notifications")

    try:
        CHROME = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=OPTIONS)
        CHROME.get(LOGIN_URL)
        time.sleep(3)

        login()
        time.sleep(1.5)

        for _ in range(4):
            lease_situation = find_consecutive_and_choose(LEASE_DATE, INI_COURT, FIN_COURT, INI_TIME, FIN_TIME)
            if lease_situation == True:
                input_Participate()
                send()
                create_lease()
            else: 
                break
            if LEASE_TOTAL_TIME < 4:
                go_back_to_lease_page()
            else:
                break

        
        with open(PWD + '.\VenueAndTimeYouLease.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(VenueAndTimeYouLease, indent=2))
        print('The rental process has ended.')
        if len(VenueAndTimeYouLease) == 0:
            print("No venue was rented. Please input valid lease_date, Court, and ini_time again.")
        time.sleep(1)
    except Exception as e:
        print("Error:", e)
    finally:
        try:
            CHROME.quit()
        except:
            pass
