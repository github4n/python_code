import common.conf as conf
import common.phone as phoneSdk
import common.randomName as nameSdk

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from concurrent.futures import ThreadPoolExecutor

import time, random, arrow, threading, uuid

import requests, queue, traceback, json, pymongo

# 链接mongodb
# myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
myclient = pymongo.MongoClient("mongodb://" + conf.mongo['host'] + ':' + conf.mongo['port'])
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

now_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')


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
        try:
            url = 'https://www.nike.com/cn/'
            requests.get(url, proxies={'https': ret.text}, timeout=10)
        except:
            msg('获取代理IP', 'IP速度过慢', '重新获取')
            num += 1
            continue

        break

    msg('获取代理IP', '成功', ret.text)

    return ret.text


# 打开浏览器
def open():
    msg("打开浏览器", '等待', '')
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
    proxies = getProxies()
    option.add_argument('proxy-server=' + proxies)

    driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe',
                              chrome_options=option)
    # 设置最大超时时间
    driver.set_page_load_timeout(30)  # seconds

    # 设置浏览器宽高
    driver.set_window_size(1760, 900)

    msg("打开浏览器", '成功', '')

    return driver


# 养号 自动浏览商品
def train(index, user):
    global NUM

    try:
        msg("线程启动", "成功", "第 " + str(index) + " 次")

        msg('获取用户', user['phone'], user['name'])

        driver = open()

        login(driver, user['phone'])

        autoPage(driver)

        # 更新数据库
        where = {
            'phone': user['phone']
        }
        ret = db_account.update_one(where, {'$set': {
            'auto_time': now_time,
        }}, upsert=True)

        if ret.acknowledged:
            msg("更新自动浏览：", "成功", "手机号：" + user['phone'] + ' 姓名：' + user['name'])
        else:
            msg("更新自动浏览：", "失败", "手机号：" + user['phone'] + ' 姓名：' + user['name'])

        NUM += 1

        msg('成功统计', '数量', NUM)

        return True
    except:
        driver.save_screenshot('nike_error/' + user['phone'] + '_' + str(arrow.now().timestamp) + '.png')
        traceback.print_exc()
    finally:
        driver.close()
        driver.quit()


# 自动浏览页面
def autoPage(driver):
    msg('自动浏览', '等待')
    time.sleep(5)

    timeout = 20

    url = 'https://store.nike.com/cn/zh_cn/pw/new-mens/meZ7pu?ipp=120'
    driver.get(url)

    num = 1
    while num <= 4:
        if num >= 4:
            msg('自动浏览', '浏览 3 个商品已完成', '切换账号')
            return True
        # 随机点击某个商品
        xpath = "//div[@class='product-name ']/p[2]"
        random_index = random.randint(1, 20)
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        dom = driver.find_elements_by_xpath(xpath)[random_index]

        # 点击商品Dom
        ActionChains(driver).move_to_element(dom).click(dom).perform()
        msg('点击商品', "索引：" + str(random_index), dom.text)

        # 获取尺码Dom
        xpath = "//div[@name='skuAndSize']/label"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_all_elements_located((By.XPATH, xpath))
        )
        dom = driver.find_elements_by_xpath(xpath)

        if dom:
            # 点击所有尺码
            size_arr = []
            for v in dom:
                size = v.text
                size_arr.append(size)

                ActionChains(driver).move_to_element(v).click(v).perform()

            msg('尺码点击', size_arr)

        msg('自动浏览', '第 ' + str(num) + ' 个商品完成', '返回列表页')
        driver.back()
        num += 1

    return True


# 鼠标随机移动
def randomMouse(driver, num=5):
    # 随机移动鼠标 防止被监控为BOT行为
    for v in range(num):
        x = random.randint(-100, 500)
        y = random.randint(-100, 500)
        ActionChains(driver).move_by_offset(x, y).perform()
        time.sleep(0.5)

    msg('鼠标随机移动', '次数', num)

    return True


# 登录
def login(driver, phone):
    try:
        msg("用户登陆", '等待', phone)

        timeout = 30

        try:
            url = 'https://www.nike.com/cn/'
            driver.get(url)
        except:
            msg('访问nike首页', '超时', '代理访问超时')
            return False

        randomMouse(driver)

        # 加入/登录Nike⁠Plus账号
        xpath = "//span[text()='加入/登录Nike⁠Plus账号']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        dom = driver.find_element_by_xpath(xpath)

        ActionChains(driver).move_to_element(dom).perform()
        dom.click()
        print("【加入/登录Nike⁠Plus账号】")

        # 填写手机号
        xpath = "//input[@placeholder='手机号码']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        driver.find_element_by_xpath(xpath).send_keys(phone)
        print("填写手机号")

        # 填写密码  统一密码
        password = 'Mn476489634'
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

        randomMouse(driver)

        # 等待登录完成
        xpath = "//*[@id='ciclp-app']"
        WebDriverWait(driver, timeout, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        msg("用户登陆", '成功', phone)

        return driver
    except:
        traceback.print_exc()
        driver.save_screenshot(phone + '_' + str(arrow.now().timestamp) + '.png')


def msg(name, status='', content='', line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    start_time = arrow.now().timestamp

    user = db_account.find().limit(100)

    # 线程索引
    threading_index = 1
    with ThreadPoolExecutor(max_workers=5) as pool:
        for i in user:
            future1 = pool.submit(train, threading_index, i)
            threading_index += 1

    end_time = arrow.now().timestamp
    use_time = end_time - start_time

    time_msg = '总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))

    msg('时间统计', time_msg, "")

    msg("运行统计", "成功", NUM)
    msg("运行统计", "失败", threading_index - NUM)
