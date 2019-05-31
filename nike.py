import common.conf as conf
import common.phone as phoneSdk
import common.randomName as nameSdk

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from concurrent.futures import ThreadPoolExecutor

import time, random, arrow, threading, uuid

import requests, queue, traceback, json, pymongo

# 链接mongodb
myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
# myclient = pymongo.MongoClient("mongodb://" + conf.mongo['host'] + ':' + conf.mongo['port'])
mydb = myclient["nike"]
db_account = mydb["account"]


# 获取代理ip
def getProxies():
    num = 1
    while num <= 3:
        proxies_api = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=6&sb=0&pb=4&mr=1&regions='
        ret = requests.get(proxies_api)
        if ret.status_code != 200:
            msg('获取代理IP', '失败', ret.status_code)
            return False

        if 'code' in ret.text:
            if ret.json()['code'] == 111:
                msg('获取代理IP', '过于频繁', '1 秒后重新获取')
                time.sleep(1)
                num += 1
                continue
        break

    msg('获取代理IP', '成功', ret.text)

    return ret.text


# 注册账号
def register(index):
    try:
        msg("线程启动", "成功", "第 " + str(index) + " 次")

        timeout = 30
        now_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')

        # 加启动配置
        option = webdriver.ChromeOptions()

        # 隐藏 "谷歌正在受到自动测试"
        option.add_argument('disable-infobars')

        # 不加载图片, 提升速度
        option.add_argument('blink-settings=imagesEnabled=false')

        # 后台运行
        # option.add_argument('headless')

        # 使用隐身模式
        option.add_argument("--incognito")

        # 使用代理
        proxies = getProxies()
        option.add_argument('proxy-server=' + proxies)

        driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe',
                                  chrome_options=option)

        driver.delete_all_cookies()

        # 设置浏览器宽高
        driver.set_window_size(1980, 900)

        try:
            url = 'https://www.ipip.net/ip.html'
            driver.get(url)
        except:
            msg('访问IP查询', '超时', '代理访问超时')
        # 获取ip地址
        xpath = "//table[2]/tbody/tr[2]/td[2]/span[1]"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        ip_address = driver.find_element_by_xpath(xpath).text
        msg('获取代理IP', '成功', ip_address)

        try:
            url = 'https://www.nike.com/cn/'
            driver.get(url)
        except:
            msg('访问nike首页', '超时', '代理访问超时')
            return False

        # 加入/登录Nike⁠Plus账号
        xpath = "//span[text()='加入/登录Nike⁠Plus账号']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【加入/登录Nike⁠Plus账号】")

        # 点击立即加入
        xpath = "//a[text()='立即加入。']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【点击立即加入】")

        # 获取手机号
        phone = phoneSdk.getPhone(723)
        if not phone:
            return False

        # 填写手机号
        xpath = "//input[@placeholder='手机号码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(phone)
        print("【填写手机号】")

        # 点击发送验证码
        xpath = "//input[@value='发送验证码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【点击发送验证码】")

        # 获取验证码
        sms = phoneSdk.getSms(phone, 723)
        if not sms:
            return False

        # 填写验证码
        xpath = "//input[@placeholder='输入验证码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(sms)
        print("【填写验证码】")

        # 点击 继续
        xpath = "//input[@value='继续']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【点击 继续】")

        # 获取姓名
        name = nameSdk.getName()

        # 填写 姓
        xpath = "//input[@placeholder='姓氏']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(name['xm'])
        print("【填写 姓】")

        # 填写 名
        xpath = "//input[@placeholder='名字']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(name['mz'])
        print("【填写 名】")

        # 填写 密码
        xpath = "//input[@placeholder='密码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        password = 'Mn476489634'
        driver.find_element_by_xpath(xpath).send_keys(password)
        print("【填写 密码】")

        # 选择 性别 男 M
        xpath = "//ul[@data-componentname='gender']/li"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_elements_by_xpath(xpath)[0].click()
        print("【选择 性别 男 M】")

        # 点击注册
        xpath = "//input[@value='注册']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【点击注册】")

        # 设置出生日日期
        random_year = '00' + str(random.randint(1990, 2000))
        random_month = '0' + str(random.randint(1, 9))
        random_day = str(random.randint(10, 25))
        random_birth = random_year + random_month + random_day
        print("获取随机出生日期：", random_birth)

        xpath = "//input[@placeholder='出生日期']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(random_birth)
        print("【设置出生日日期：", random_birth)

        # 设置邮箱
        email_random = str(arrow.now().timestamp)
        email_main = 'levislin2016+' + email_random + '@gmail.com'
        print("获取无限域名地址：", email_main)

        xpath = "//input[@placeholder='电子邮件']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(email_main)
        print("【设置电子邮件】：", email_main)

        # 点击保存 登陆
        xpath = "//input[@value='保存']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【点击保存 登陆】")

        phoneSdk.ignore(phone, 723)

        # 插入数据库
        data = {
            'phone': phone,
            'name': name['xm'] + name['mz'],
            'address': "",
            'refresh_token': "",
            'birthday': random_birth,
            'email': email_main,
            'access_token': "",
            'step': 'register',
            'ip_address': ip_address,
            'time': arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss'),
        }
        ret = db_account.insert_one(data)
        if ret.acknowledged:
            print("保存账号成功", 200, data)
        else:
            print("保存账号失败", 500, data)

        setAddress(driver, phone)

        refresh_token = getRefreshToken(driver, phone)

        getAccessToken(phone, refresh_token, proxies)

        return True



    except:
        driver.save_screenshot('nike_error/' + phone + '_' + str(arrow.now().timestamp) + '.png')
        traceback.print_exc()
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
            'step': 'refresh_token',
        }}, upsert=True)

        if ret.acknowledged:
            print("更新RefreshToken：", "成功", "手机号：", phone)
        else:
            print("更新RefreshToken：", "失败", "手机号：", phone)

        return refresh_token
    except:
        traceback.print_exc()
        driver.save_screenshot('nike_error/' + phone + '_' + str(arrow.now().timestamp) + '.png')

        return False


# 获取access_token
def getAccessToken(phone, refresh_token, proxies):
    Timeout = 20

    url = 'https://api.nike.com/idn/shim/oauth/2.0/token'
    json = {
        'client_id': 'HlHa2Cje3ctlaOqnxvgZXNaAs7T9nAuH',
        'grant_type': 'refresh_token',
        'ux_id': 'com.nike.commerce.snkrs.ios',
        'refresh_token': refresh_token,
    }
    proxies = {
        'https': proxies,
    }

    num = 1
    while num <= 3:
        try:
            ret = requests.post(url, json=json, timeout=Timeout, proxies=proxies)
            break
        except:
            proxies = {
                'https': proxies,
            }

            msg('获取AccessToken', ret.status_code, '代理连接失败')
            num += 1
            continue
    try:
        access_token = ret.json()['access_token']
    except:
        access_token = ret.json()
        msg('更新AccessToken', 500, ret.json())

    # 更新数据库
    where = {
        'phone': phone
    }
    ret = db_account.update_one(where, {'$set': {
        'access_token': access_token,
        'step': 'access_token',
    }}, upsert=True)

    if ret.acknowledged:
        msg("更新AccessToken：", "成功", access_token)
    else:
        msg("更新AccessToken：", "失败", access_token)

    return access_token


def setAddress(driver, phone):
    time.sleep(5)

    timeout = 20

    num = 1
    while num <= 4:
        if num == 4:
            return False
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
            driver.get("https://www.nike.com/cn/")
            time.sleep(1)
            num += 1
            continue

    # 设置默认配送地址
    xpath = "//*[text()='将其设为我的默认配送地址']"
    WebDriverWait(driver, timeout, 0.5).until(
        EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.find_element_by_xpath(xpath).click()
    print("【设置默认配送地址】")

    set_num = 1
    while set_num <= 3:
        try:
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
            driver.find_element_by_xpath(xpath).clear()
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
                'step': 'address',
            }}, upsert=True)

            if ret.acknowledged:
                print("设置配送地址：", "成功", "手机号：", phone)
            else:
                print("设置配送地址：", "失败", "手机号：", phone)

            return address
        except:
            traceback.print_exc()
            driver.save_screenshot('nike_error/' + phone + '_' + str(arrow.now().timestamp) + '.png')
            set_num += 1


def msg(name, status, content, line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
    mydb = myclient["du"]
    db_nike = mydb["nike"]

    # 线程索引
    threading_index = 1
    with ThreadPoolExecutor(max_workers=5) as pool:
        for i in range(20):
            future1 = pool.submit(register, threading_index)
            threading_index += 1
