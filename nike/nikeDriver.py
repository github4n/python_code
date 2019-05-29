import common.conf as conf
import common.randomName as nameSdk

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import time, json, traceback, pymongo, random,arrow

# 链接mongodb
myclient = pymongo.MongoClient("mongodb://" + conf.mongo['host'] + ':' + conf.mongo['port'])
mydb = myclient["nike"]
db_account = mydb["account"]


def open():
    print("正在打开浏览器")
    # 加启动配置
    option = webdriver.ChromeOptions()

    # 隐藏 "谷歌正在受到自动测试"
    option.add_argument('disable-infobars')

    # 禁止加载图片
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # option.add_experimental_option("prefs", prefs)

    # 后台运行
    option.add_argument('--headless')

    # 使用隐身模式
    option.add_argument("--incognito")

    # driver = webdriver.Chrome(executable_path='./driver/chromedriver_74.exe', desired_capabilities=capabilities,
    #                           chrome_options=option)

    driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe', chrome_options=option)

    # 设置浏览器宽高
    driver.set_window_size(1980, 1366)

    return driver


def login(phone):
    try:
        driver = open()

        print("开始登陆")
        url = 'https://www.nike.com/cn/zh_cn/s/register'
        driver.get(url)

        timeout = 30

        # 统一密码
        password = 'Mn476489634'

        # 填写手机号
        xpath = "//input[@placeholder='手机号码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        driver.find_element_by_xpath(xpath).send_keys(phone)
        print("填写手机号")

        # 填写密码
        xpath = "//input[@placeholder='密码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        driver.find_element_by_xpath(xpath).send_keys(password)
        print("填写密码")

        # 点击登录
        xpath = "//input[@value='登录']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.find_element_by_xpath(xpath).click()
        print("点击登录")

        # 等待登录完成
        xpath = "//*[@id='ciclp-app']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        print("登录成功")

        # 设置配送地址
        address = setAddress(driver, phone)
        if not address:
            return False
        refresh_token = getRefreshToken(driver, phone)
        if not refresh_token:
            return False

        return refresh_token
    except:
        traceback.print_exc()
        driver.save_screenshot(phone + '_' + str(arrow.now().timestamp) + '.png')
    finally:
        driver.close()
        driver.quit()


# 获取用户refresh_token
def getRefreshToken(driver, phone):
    try:
        url = 'https://unite.nike.com/session.html'
        driver.get(url)

        # 获取用户refreshToken
        js = "return localStorage.getItem('com.nike.commerce.nikedotcom.web.credential');"
        userInfo = driver.execute_script(js)
        cookie_arr = json.loads(userInfo)

        refresh_token = cookie_arr['refresh_token']

        # 更新数据库
        where = {
            'phone': phone
        }
        ret = db_account.update_one(where, {'$set': {
            'refresh_token': refresh_token,
        }}, upsert=True)

        if ret.acknowledged:
            print("更新RefreshToken：", "成功", "手机号：", phone)
        else:
            print("更新RefreshToken：", "失败", "手机号：", phone)

        return refresh_token
    except:
        traceback.print_exc()
        driver.save_screenshot(phone + '_' + str(arrow.now().timestamp) + '.png')

        return False


def setAddress(driver, phone):
    timeout = 20

    num = 1
    while num <= 3:
        try:
            # 跳转地址设置
            driver.get("https://www.nike.com/member/settings/addresses")
            print("【跳转地址设置】")

            # 点击添加配送地址
            xpath = "//*[@class='ncss-btn-secondary-dark d-sm-h d-md-ib']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.find_elements_by_xpath(xpath)[2].click()
            print("【点击添加配送地址】")
            break
        except:
            time.sleep(1)
            num += 1
            continue
    try:
        # 设置默认配送地址
        xpath = "//*[text()='将其设为我的默认配送地址']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【设置默认配送地址】")

        name = nameSdk.getName()
        # 填写 姓
        xpath = "//input[@name='姓氏']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(name['xm'])
        time.sleep(1)
        driver.find_element_by_xpath(xpath).clear()
        driver.find_element_by_xpath(xpath).send_keys(name['xm'])
        time.sleep(1)
        driver.find_element_by_xpath(xpath).clear()
        driver.find_element_by_xpath(xpath).send_keys(name['xm'])
        print("【填写 姓】")

        # 填写 名
        xpath = "//input[@name='名字']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(name['mz'])
        time.sleep(0.5)
        driver.find_element_by_xpath(xpath).clear()
        driver.find_element_by_xpath(xpath).send_keys(name['mz'])
        print("【填写 名】")

        # 选择省份 江苏省
        xpath = "//*[@id='省份']/option[@value='CN-32']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【选择省份 江苏省】")

        # 选择城市 徐州市
        xpath = "//*[@id='城市']/option[@value='徐州市']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【选择城市 徐州市】")

        # 选择乡镇区县 贾汪区
        xpath = "//*[@id='乡镇区县']/option[@value='贾汪区']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【选择乡镇区县 贾汪区】")

        # 填写 地址一
        address = ['大泉街道', '老矿街道', '工业园区管委会', '江庄街道']
        address = random.choice(address)
        address_random = nameSdk.getAddress()
        address = address + address_random
        print("【获取地址】：", address)

        xpath = "//*[@id='地址 1']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(address)
        time.sleep(0.5)
        driver.find_element_by_xpath(xpath).clear()
        driver.find_element_by_xpath(xpath).send_keys(address)

        # 填写电话号码
        xpath = "//*[@id='电话号码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(phone)
        print("【填写电话号码】")

        # 点击保存
        xpath = "//*[text()='保存']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()

        # 等待完成
        xpath = "//p[text()='配送地址']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))

        # 更新数据库
        where = {
            'phone': phone
        }
        ret = db_account.update_one(where, {'$set': {
            'address': address,
        }}, upsert=True)

        if ret.acknowledged:
            print("设置配送地址：", "成功", "手机号：", phone)
        else:
            print("设置配送地址：", "失败", "手机号：", phone)

        return address

    except:
        traceback.print_exc()
        driver.save_screenshot(phone + '_' + str(arrow.now().timestamp) + '.png')
        return False
