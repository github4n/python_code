import common.phone as phoneSdk

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from faker import Faker

from concurrent.futures import ThreadPoolExecutor

import time, random, arrow, threading, uuid

import requests, queue, traceback, json, pymongo

# 链接mongodb
myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
# myclient = pymongo.MongoClient("mongodb://" + conf.mongo['host'] + ':' + conf.mongo['port'])
mydb = myclient["nike"]
db_account = mydb["account"]

HOST = "https://unite.nike.com/"

PARAMS = {
    'appVersion': "595",
    'experienceVersion': "493",
    'uxId': "com.nike.commerce.nikedotcom.web",
    'locale': "zh_CN",
    'backendEnvironment': "identity",
    'browser': "Google Inc.",
    'os': "undefined",
    'mobile': "false",
    'native': "false",
    'visit': "3",
    'language': 'zh-Hans',
}

NUM = 0

fake = Faker('zh_CN')


# 获取代理ip
def getProxies():
    num = 1
    while num <= 5:
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

        msg('获取代理IP', '成功', ret.text)

        return ret.text

    return False




# 注册账号
def register(index):
    global NUM
    try:
        msg("线程启动", "成功", "第 " + str(index) + " 次")

        num = 1
        while num <= 3:
            try:
                url = 'https://www.nike.com/cn/'

                proxies = getProxies()

                requests.get(url, proxies={'https': proxies}, timeout=10)
            except:
                msg('获取代理IP', 'IP速度过慢', '重新获取')
                num += 1
                continue

            break

        timeout = 10

        # 加启动配置
        option = webdriver.ChromeOptions()

        # 隐藏 "谷歌正在受到自动测试"
        option.add_argument('disable-infobars')

        # 不加载图片, 提升速度
        option.add_argument('blink-settings=imagesEnabled=false')

        # 后台运行
        option.add_argument('headless')

        # 使用隐身模式
        option.add_argument("--incognito")

        # 使用代理
        option.add_argument('proxy-server=' + proxies)

        driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe',
                                  chrome_options=option)
        # 设置最大超时时间
        driver.set_page_load_timeout(30)  # seconds

        # 删除所有cookie
        driver.delete_all_cookies()

        # 设置浏览器宽高
        driver.set_window_size(1980, 900)

        try:
            url = 'https://www.nike.com/cn/'
            driver.get(url)
        except:
            msg('访问nike首页', '超时', '代理访问超时')
            return False

        # 加入/登录Nike⁠Plus账号
        xpath = "//span[text()='加入/登录Nike⁠Plus账号']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.click()
        print("【加入/登录Nike⁠Plus账号】")

        # 点击立即加入
        xpath = "//a[text()='立即加入。']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.click()
        print("【点击立即加入】")

        try_num = 1
        while try_num <= 4:
            if try_num == 4:
                msg('手机验证步骤', '重试次数已达3次', '退出浏览器')
                return False
            # 获取手机号
            phone = phoneSdk.getPhone(723)
            if not phone:
                try_num += 1
                continue

            # 填写手机号
            xpath = "//input[@placeholder='手机号码']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            dom = driver.find_element_by_xpath(xpath)

            ActionChains(driver).move_to_element(dom).perform()
            dom.clear()
            dom.send_keys(phone)
            print("【填写手机号】")

            # 随机移动鼠标 防止被监控为BOT行为
            randomMouse(driver)

            # 点击发送验证码
            xpath = "//input[@value='发送验证码']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            dom = driver.find_element_by_xpath(xpath)

            ActionChains(driver).move_to_element(dom).perform()
            dom.click()
            print("【点击发送验证码】")

            # 获取验证码
            sms = phoneSdk.getSms(phone, 723)
            if not sms:
                try_num += 1
                continue

            # 填写验证码
            xpath = "//input[@placeholder='输入验证码']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            dom = driver.find_element_by_xpath(xpath)

            ActionChains(driver).move_to_element(dom).perform()
            dom.clear()
            dom.send_keys(sms)
            print("【填写验证码】")

            break

        # 点击 继续
        xpath = "//input[@value='继续']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.click()
        print("【点击 继续】")

        # 获取随机姓名
        name = {
            'xm': fake.last_name(),
            'mz': fake.first_name(),
        }
        print("【随机姓名】：", name['xm'] + name['mz'])

        # 填写 姓
        xpath = "//input[@placeholder='姓氏']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.send_keys(name['xm'])
        print("【填写 姓】")

        # 填写 名
        xpath = "//input[@placeholder='名字']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.send_keys(name['mz'])
        print("【填写 名】")

        # 填写 密码
        password = 'Mn476489634'

        xpath = "//input[@placeholder='密码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.send_keys(password)
        print("【填写 密码】")

        # 选择 性别 男 M
        xpath = "//ul[@data-componentname='gender']/li"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        sex_num = random.randint(0, 1)
        driver.find_elements_by_xpath(xpath)[sex_num].click()
        print("【选择 性别】：", sex_num)

        # 随机移动鼠标 防止被监控为BOT行为
        randomMouse(driver)

        # 点击注册
        xpath = "//input[@value='注册']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.click()
        print("【点击注册】")

        # 随机移动鼠标 防止被监控为BOT行为
        randomMouse(driver)

        # 设置出生日日期
        random_year = '00' + str(random.randint(1990, 2000))
        random_month = '0' + str(random.randint(1, 9))
        random_day = str(random.randint(10, 25))
        random_birth = random_year + random_month + random_day
        print("获取随机出生日期：", random_birth)

        xpath = "//input[@placeholder='出生日期']"
        WebDriverWait(driver, 20, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(random_birth)
        print("【设置出生日日期：", random_birth)

        # 设置邮箱 无限影子邮箱+转发
        email = str(phone) + '@rank666.uu.ma'
        print("获取无限域名地址：", email)

        xpath = "//input[@placeholder='电子邮件']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).send_keys(email)
        print("【设置电子邮件】：", email)

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
            'email': email,
            'access_token': "",
            'step': 'register',
            'time': arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss'),
        }
        ret = db_account.insert_one(data)
        if ret.acknowledged:
            print("保存账号成功", 200, data)
        else:
            print("保存账号失败", 500, data)

        time.sleep(5)

        refresh_token = getRefreshToken(driver, phone)
        if not refresh_token:
            return False

        address = setAddress(driver, phone)
        if not address:
            return False

        access_token = getAccessToken(phone, refresh_token, proxies)
        if not access_token:
            return False

        setting = getSetting(access_token, proxies)
        if not setting:
            return False

        set_api = setSetttingApi(setting, access_token, proxies)
        if not set_api:
            return False

        NUM += 1

        msg('成功统计', '数量', NUM)

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
            msg("更新RefreshToken：", "成功", "手机号：" + str(phone))
        else:
            msg("更新RefreshToken：", "失败", "手机号：" + str(phone))

        return refresh_token
    except:
        traceback.print_exc()
        driver.save_screenshot('nike_error/' + phone + '_' + str(arrow.now().timestamp) + '.png')
        return False


# 获取access_token
def getAccessToken(phone, refresh_token, proxies):
    if not phone:
        msg('获取AccessToken', '失败', 'phone 不能为空,phone:' + str(phone))
        return False

    if not refresh_token:
        msg('获取AccessToken', '失败', 'refresh_token 不能为空,refresh_token:' + str(refresh_token))
        return False

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
            try:
                access_token = ret.json()['access_token']
            except:
                msg('获取AccessToken', 500, ret.json())
                return False

            msg('获取AccessToken', '成功', access_token)

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
            break
        except:
            new_proxies = getProxies()

            msg('获取AccessToken', '代理超时', '代理连接失败,重新获取代理ip:' + new_proxies)

            proxies = {
                'https': new_proxies,
            }

            num += 1
            continue

    return False




def setAddress(driver, phone):
    time.sleep(5)

    timeout = 15

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
            print("重新访问地址设置", "第 " + str(num) + " 次")
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
            name = {
                'xm': fake.last_name(),
                'mz': fake.first_name(),
            }
            print("【随机姓名】：", name['xm'] + name['mz'])

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

            # 填写 地址一 随机地址
            address = getRandomAddress()

            xpath = "//*[@id='地址 1']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            driver.find_element_by_xpath(xpath).send_keys(address)
            time.sleep(0.5)
            driver.find_element_by_xpath(xpath).clear()
            driver.find_element_by_xpath(xpath).send_keys(address)

            # 填写邮政编码
            postage_code = '221011'
            xpath = "//*[@id='邮政编码']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            driver.find_element_by_xpath(xpath).clear()
            driver.find_element_by_xpath(xpath).send_keys(postage_code)
            print("【填写邮政编码】")

            # 填写电话号码
            xpath = "//*[@id='电话号码']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            driver.find_element_by_xpath(xpath).clear()
            driver.find_element_by_xpath(xpath).send_keys(phone)
            print("【填写电话号码】")

            # 点击保存
            xpath = "//*[text()='保存']"
            WebDriverWait(driver, 5, 0.5).until(
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


def getRandomAddress():
    # 随机街道
    address = ['大泉街道', '老矿街道', '工业园区管委会', '江庄街道']
    address = random.choice(address)
    # 随机地址
    address_random = fake.street_address()
    # 随机地址详情
    address_detail1 = str(random.randint(1, 9)) + '栋'
    address_detail2 = str(random.randint(1, 6)) + '单元'
    address_detail3 = str(random.randint(1, 32)) + str(random.randint(1, 2)) + str(random.randint(1, 10)) + '室'

    address = address + address_random + address_detail1 + address_detail2 + address_detail3

    msg('获取随机地址', address)

    return address


# 获取设置信息
def getSetting(access_token, proxies=''):
    url = 'https://idn.nike.com/user/mexaccountsettings'

    headers = {"authorization": "Bearer " + access_token}

    proxies = {
        'https': proxies,
    }

    num = 1
    while num <= 3:
        try:
            ret = requests.get(url, timeout=20, headers=headers, proxies=proxies)
            if ret.status_code != 200:
                msg('获取设置信息接口异常', ret.status_code, ret.text)
                return False

            msg('获取设置信息成功', '成功')
            # print(json.dumps(ret.json(), sort_keys=True, indent=4, separators=(', ', ': ')))

            return ret.json()
        except:
            new_proxies = getProxies()

            msg('获取设置信息', '代理超时', '代理连接失败,重新获取代理ip:' + new_proxies)

            proxies = {
                'https': new_proxies,
            }

            num += 1
            continue

    return False


def setSetttingApi(phone, setting, access_token, proxies=''):
    url = 'https://idn.nike.com/user/mexaccountsettings'

    camAddressId = setting['address']['shipping']['camAddressId']
    guid = setting['address']['shipping']['guid']
    address = getRandomAddress()
    email = phone + '@rank666.uu.ma'
    json = {
        "address": {
            "shipping": {
                "camAddressId": camAddressId,
                "code": "000000",
                "country": "CN",
                "guid": guid,
                "line1": address,
                "line2": "",
                "line3": "",
                "locality": "徐州市",
                "phone": {
                    "primary": phone
                },
                "preferred": True,
                "province": "CN-32",
                "zone": "贾汪区",
                "type": "SHIPPING",
                "name": {
                    "primary": {
                        "family": fake.last_name(),
                        "given": fake.first_name()
                    }
                }
            }
        },
        'username': email,
    }

    headers = {
        "authorization": "Bearer " + access_token,
    }

    proxies = {
        'https': proxies,
    }

    num = 1
    while num <= 3:
        try:
            ret = requests.put(url, json=json, timeout=20, headers=headers, proxies=proxies)
            if ret.status_code != 202:
                msg('设置地址接口异常', ret.status_code, ret.text)
                return False

            msg('设置地址接口成功', ret.status_code, json)
            break
        except:
            new_proxies = getProxies()

            msg('设置信息接口', '代理超时', '代理连接失败,重新获取代理ip:' + new_proxies)

            proxies = {
                'https': new_proxies,
            }

            num += 1
            continue



    # 更新数据库
    where = {
        'phone': phone
    }
    ret = db_account.update_one(where, {'$set': {
        'address': address,
        'email': email,
        'step': 'setting',
        'time': arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss'),
    }}, upsert=True)

    if ret.acknowledged:
        print("数据库设置配送地址：", "成功", "手机号：", phone)
    else:
        print("数据库设置配送地址：", "失败", "手机号：", phone)

    return True


# 获取用户信息
def getUser(access_token, proxies=''):
    url = HOST + 'getUserService'
    headers = {"authorization": "Bearer " + access_token}

    PARAMS['viewId'] = 'unite'
    PARAMS['atgSync'] = 'true'

    proxies = {
        'https': proxies,
    }

    num = 1
    while num <= 3:
        try:
            ret = requests.post(url, json=json, timeout=20, headers=headers, proxies=proxies)
            break
        except:
            new_proxies = getProxies()

            msg('设置信息接口', ret.status_code, '代理连接失败,重新获取代理ip:' + new_proxies)

            proxies = {
                'https': new_proxies,
            }

            num += 1
            continue

    if ret.status_code != 200:
        msg('获取用户信息接口异常', ret.status_code, ret.text)
        return False

    msg('获取用户信息成功', ret.status_code)
    print(json.dumps(ret.json(), sort_keys=True, indent=4, separators=(', ', ': ')))

    return ret.json()


# 鼠标随机移动
def randomMouse(driver):
    msg('鼠标曲线移动移动', '开始')

    # 随机移动鼠标 防止被监控为BOT行为
    mouse_arr = [{'x': 822, 'y': 525}, {'x': 668, 'y': 535}, {'x': 641, 'y': 537}, {'x': 682, 'y': 541},
                 {'x': 711, 'y': 540}, {'x': 736, 'y': 538}, {'x': 769, 'y': 537}, {'x': 792, 'y': 533},
                 {'x': 821, 'y': 531}, {'x': 855, 'y': 524}, {'x': 887, 'y': 523}, {'x': 918, 'y': 521},
                 {'x': 944, 'y': 517}, {'x': 968, 'y': 514}, {'x': 1005, 'y': 503}, {'x': 1032, 'y': 498},
                 {'x': 1062, 'y': 494}, {'x': 1077, 'y': 491}, {'x': 1111, 'y': 487}, {'x': 1144, 'y': 482},
                 {'x': 1187, 'y': 476}, {'x': 1239, 'y': 468}, {'x': 1290, 'y': 455}, {'x': 1355, 'y': 431},
                 {'x': 1409, 'y': 402}, {'x': 1433, 'y': 393}, {'x': 1462, 'y': 379}, {'x': 1500, 'y': 363},
                 {'x': 1527, 'y': 349}, {'x': 1574, 'y': 323}, {'x': 1600, 'y': 309}, {'x': 1624, 'y': 298},
                 {'x': 1648, 'y': 286}, {'x': 1682, 'y': 268}, {'x': 1715, 'y': 248}, {'x': 1736, 'y': 235},
                 {'x': 1769, 'y': 208}, {'x': 1790, 'y': 192}, {'x': 1798, 'y': 187}, {'x': 1819, 'y': 173},
                 {'x': 1841, 'y': 147}, {'x': 1851, 'y': 134}, {'x': 1862, 'y': 121}, {'x': 1871, 'y': 107},
                 {'x': 1879, 'y': 93}, {'x': 1886, 'y': 81}, {'x': 1887, 'y': 79}, {'x': 1885, 'y': 79},
                 {'x': 1870, 'y': 88}, {'x': 1824, 'y': 115}, {'x': 1802, 'y': 133}]
    for v in mouse_arr:
        ActionChains(driver).move_by_offset(v['x'], v['y']).perform()
        time.sleep(0.1)

    msg('鼠标曲线移动移动', '结束')

    return True


def msg(name='', status='', content='', line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    start_time = arrow.now().timestamp

    # 线程索引
    threading_index = 1
    with ThreadPoolExecutor(max_workers=10) as pool:
        for i in range(10):
            future1 = pool.submit(register, threading_index)
            threading_index += 1

    end_time = arrow.now().timestamp
    use_time = end_time - start_time

    time_msg = '总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))

    msg('时间统计', time_msg, "")

    msg("运行统计", "成功", NUM)
    msg("运行统计", "失败", threading_index - NUM)
