import ys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from concurrent.futures import ThreadPoolExecutor

import common.phone as phoneSdk
import common.randName as nameSdk
import time, random, arrow, threading

import requests, pymongo, queue,traceback
from multiprocessing import Pool, Queue

PROXIES_API = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=6&sb=0&pb=4&mr=1&regions='


# def login():
#     login_dom = "//li[@class='member-nav-item has-submenu d-sm-ib va-sm-m']/div"
#
#     myaccount_dom = "//div[@id='AccountNavigationDropdown']"
#     is_show = driver.find_element_by_xpath(myaccount_dom).is_displayed()
#     print(is_show)
#
#     # 点击显示登录框
#     driver.find_element_by_xpath(login_dom).click()
#
#     # 输入手机号
#     dom_phone = "//input[@placeholder='手机号码']"
#     driver.find_element_by_xpath(dom_phone).send_keys('18968804688')
#
#     # 输入密码
#     dom_phone = "//input[@placeholder='密码']"
#     driver.find_element_by_xpath(dom_phone).send_keys('Mn476489634')
#
#     # 点击登录
#     login_dom = "//input[@value='登录']"
#     driver.find_element_by_xpath(login_dom).click()
#
#     # 判断是否登录
#     check_num = 1
#     while check_num <= 5:
#         time.sleep(5)
#
#         is_show = driver.find_element_by_xpath(myaccount_dom).is_displayed()
#         if not is_show:
#             print("正在检测登录状态", "第 " + str(check_num) + " 次")
#             check_num += 1
#             continue
#         print("登录成功")
#         break
#
#     # 跳转需要抽奖的鞋子
#     url = 'https://www.nike.com/cn/launch/t/'
#     name = 'air-max-tailwind-4-digi-camo'
#     url = url + name
#
#     driver.get(url)
#
#     time.sleep(10)
#     # 点击抽奖
#     js = "document.getElementsByClassName('buying-tools-container').firstChild.click()"
#     driver.execute_script(js)


# 获取代理ip
def getProxies():
    ret = requests.get(PROXIES_API)
    if ret.status_code != 200:
        print('获取代理IP', ret.status_code, '获取代理ip失败', ret.text)

    print('获取代理IP', ret.status_code, '成功', ret.text)

    return ret.text


# 注册账号
def register(db_nike):
    try:
        # print("线程启动 第 " + str(i) + " 次")

        timeout = 30
        now_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
        capabilities = dict(DesiredCapabilities.CHROME)
        capabilities['proxy'] = {'proxyType': 'MANUAL',
                                 'httpProxy': getProxies(),
                                 'class': "org.openqa.selenium.Proxy",
                                 'autodetect': False}

        # 加启动配置
        option = webdriver.ChromeOptions()
        # 隐藏 "谷歌正在受到自动测试"
        option.add_argument('disable-infobars')
        # 不加载图片, 提升速度
        option.add_argument('blink-settings=imagesEnabled=false')
        # 后台运行
        # option.add_argument('headless')
        # 开启实验性功能参数
        # option.add_experimental_option('excludeSwitches', ['enable-automation'])

        driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe', desired_capabilities=capabilities,
                                  chrome_options=option)
        # driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe', chrome_options=option)
        # 窗口最大化
        driver.maximize_window()

        driver.get('https://www.nike.com/cn/zh_cn/s/register')

        time.sleep(10)

        # 点击立即加入
        xpath = "//a[text()='立即加入。']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【点击立即加入】")

        # 获取手机号
        phone = phoneSdk.Phone.getPhone(723)

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

        sms_num = 1
        while sms_num <= 3:
            # 等待获取验证码
            sms = phoneSdk.Phone.getSms(phone, 723)
            if not sms:
                print("【获取验证码】超时", "第 " + str(sms_num) + " 次")
                # 点击发送验证码
                driver.find_element_by_xpath(xpath).click()
                sms_num += 1
                continue
            break

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

        # 点击跳过 这样才能登陆
        xpath = "//input[@value='跳过']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【点击跳过 这样才能登陆】")

        # 跳转地址设置
        driver.get("https://www.nike.com/member/settings/addresses")
        print("【跳转地址设置】")

        # 点击添加配送地址
        xpath = "//*[@class='ncss-btn-secondary-dark d-sm-h d-md-ib']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_elements_by_xpath(xpath)[2].click()
        print("【点击添加配送地址】")

        # 设置默认配送地址
        xpath = "//*[text()='将其设为我的默认配送地址']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        print("【设置默认配送地址】")

        # 填写 姓
        xpath = "//input[@name='姓氏']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
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
        print("【点击保存】")

        info = {
            '账号/手机': str(phone),
            '密码': password,
            '姓名': name['xm'] + name['mz'],
            '地址': address,
            '时间': now_time
        }

        print("【注册成功】：", info)
        db_nike.insert_one(info)

        phoneSdk.Phone.ignore(phone, 723)
        time.sleep(5)
        driver.quit()
    except:
        driver.get_screenshot_as_file(now_time + '.png')
        traceback.print_exc()
        driver.quit()


class ThreadPool(object):
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._q = queue.Queue(self.maxsize)
        for i in range(self.maxsize):
            self._q.put(threading.Thread)

    def getThread(self):
        return self._q.get()

    def addThread(self):
        self._q.put(threading.Thread)


# 开启线程
def threadPay(num=0):
    # 生成bp
    task_number = 15

    if num != 0:
        task_number = num

    print(num)
    i = 1
    tasks = []

    myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
    mydb = myclient["du"]
    db_nike = mydb["nike"]

    # # 开启 ip池线程
    # t_ip = threading.Thread(target=proxiesPool)
    # t_ip.start()
    #
    # # 开启 鞋子尺码维护池
    # t_shoes = threading.Thread(target=search)
    # t_shoes.start()

    while i <= task_number:
        print('开启 第 ' + str(num) + " 线程", 200, '成功', '成功')

        # 开启线程
        t = threading.Thread(target=register, args=(db_nike,))
        tasks.append(t)
        t.start()

        i += 1


if __name__ == '__main__':
    myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
    mydb = myclient["du"]
    db_nike = mydb["nike"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i in range(200):
            future1 = pool.submit(register, db_nike)

