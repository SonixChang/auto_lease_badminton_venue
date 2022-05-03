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

    with open(PWD + "\captcha_login.png", 'wb') as image:
        image.write(base64.b64decode(img_base64))
    ocr = ddddocr.DdddOcr()
    with open(PWD + '\captcha_login.png', 'rb') as f:
        img_bytes = f.read()
    captcha = ocr.classification(img_bytes) # 驗證碼
    os.remove(PWD + '\captcha_login.png')
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


def search_all_time_interval_by_specify_date(date_choose: str):
    DATE = Select(CHROME.find_element_by_id('RentalData'))
    VENUE = {}
    DATEBOX = {}
    DATEBOX["Available Time"] = {}

    for venu_num in range(727, 737): # 選場地
        venue_id = f"SubVenues_{venu_num}"
        venu_num -= 726
        VENUE[venue_id] = f"Court {venu_num}"

    for date_item in DATE.options: # 選時間
        if date_choose == date_item.text:        
            DATE.select_by_value(date_item.text)
            time.sleep(1)
            DATEBOX[date_item.text] = {}

            for venu_num in range(727, 737): # 選場地
                venue_id = f"SubVenues_{venu_num}"
                CHROME.find_element_by_id(venue_id).click()
                time.sleep(1.5)

                time_interval = CHROME.find_elements_by_class_name("BookB.UnBooked")
    
                DATEBOX[date_item.text][VENUE[venue_id]] = []
                
                for times in time_interval:
                    DATEBOX[date_item.text][VENUE[venue_id]].append(times.text)

            for court in DATEBOX[date_item.text].keys(): # 寫入DATEBOX["Available Time"]
                DATEBOX["Available Time"][court] = []

                time_interval = DATEBOX[date_item.text][court]
                for times in time_interval:
                    if time_interval.index(times) == 0:
                        continue
                    cure_ini_time = times[:5]
                    last_fin_time = time_interval[time_interval.index(times)-1][-5:]

                    if cure_ini_time == last_fin_time:    # 判斷是否連續
                        if time_interval[time_interval.index(times)-1] not in DATEBOX["Available Time"][court]:
                            DATEBOX["Available Time"][court].append(time_interval[time_interval.index(times)-1])
                        DATEBOX["Available Time"][court].append(times)
    
    print(json.dumps(DATEBOX, indent=2))


def find_consecutive_and_choose(date_choose: str, ini_court: int, fin_court: int, specify_ini_time: int):
    DATE = Select(CHROME.find_element_by_id('RentalData'))
    VENUE = {}
    VenueAndTimeYouLease = {}
    TwoHours = True

    for venu_num in range(ini_court, fin_court + 1): # 建立場地dict
        venu_num += 726
        venue_id = f"SubVenues_{venu_num}"
        venu_num -= 726
        VENUE[venue_id] = f"Court {venu_num}"
    
    for date_item in DATE.options: # 選時間

        if date_choose == date_item.text:        
            DATE.select_by_value(date_item.text)
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
                        if int(times.text[:2]) == specify_ini_time: # 指定起始時間
                            cure_fin_time = times.text[-5:]
                            next_ini_time = time_interval[time_interval.index(times)+1].text[:5]
                            if cure_fin_time == next_ini_time:    # 判斷是否連續
                                if time_interval[time_interval.index(times)+1].text not in VenueAndTimeYouLease:  # 前一'網頁元素'判斷(可以改成'時間區間')
                                    times.click()
                                    time_interval[time_interval.index(times)+1].click()
                                    
                                    VenueAndTimeYouLease[VENUE[venue_id]] = []
                                    VenueAndTimeYouLease[VENUE[venue_id]].append(times.text)
                                    VenueAndTimeYouLease[VENUE[venue_id]].append(time_interval[time_interval.index(times)+1].text)
                                    print(VenueAndTimeYouLease)
                                    return                        # 有租到就終止副程式
            
            TwoHours = False
            for venu_num in range(ini_court, fin_court + 1): # 選場地
                venu_num += 726
                venue_id = f"SubVenues_{venu_num}"
                CHROME.find_element_by_id(venue_id).click()
                time.sleep(1.5)

                time_interval = CHROME.find_elements_by_class_name("BookB.UnBooked")
                
                if TwoHours == False:
                    for times in time_interval:  # 租1hr
                        if int(times.text[:2]) == specify_ini_time or int(times.text[:2]) == specify_ini_time + 1:
                            times.click()
                            VenueAndTimeYouLease[VENUE[venue_id]] = []
                            VenueAndTimeYouLease[VENUE[venue_id]].append(times.text)
                            print(VenueAndTimeYouLease)
                            return
    
    print("No venue was rented. Please input valid lease_date, Court, and ini_time again.")
    CHROME.quit()
    exit()


def input_Participate():
    CHROME.find_element_by_id("ParticipateTypeG").send_keys(GENERAL_STATUS)
    CHROME.find_element_by_id("ParticipateTypeP").send_keys(PREFERENTIAL_STATUS)


def send():
    CHROME.find_element_by_name("Send").click()
    time.sleep(1)
    CHROME.find_element_by_name("Send").click()


def create_lease():
    CHROME.find_element_by_id("Agree").click()
    CHROME.find_element_by_class_name("Btn.Send").click()
    # time.sleep(0.5)
    # CHROME.find_element_by_name("Send").click()


if __name__ == '__main__':
    PWD = os.path.dirname(__file__)
    print(PWD)
    with open(PWD + '\input.json', 'r', encoding='utf-8') as f:
        InputData = json.load(f)

    LOGIN_URL = InputData['login_url']
    MAIL = InputData['mail']
    PASSWORD = InputData['password']
    
    LEASE_DATE = InputData['lease_date']
    INI_COURT = InputData['ini_court']
    FIN_COURT = InputData['fin_court']
    INI_TIME = InputData['ini_time']
    GENERAL_STATUS = InputData['general_status'] # 一般身分人數
    PREFERENTIAL_STATUS = InputData['preferential_status'] # 優待身分人數

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

        find_consecutive_and_choose(LEASE_DATE, INI_COURT, FIN_COURT, INI_TIME)
        input_Participate()
        send()
        time.sleep(3)

        create_lease()
        time.sleep(3)
    except Exception as e:
        print("Error:", e)
    finally:
        try:
            CHROME.quit()
        except:
            pass
