import common.conf as conf
import common.phone as phoneSdk
import common.randomName as nameSdk

import nike

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from concurrent.futures import ThreadPoolExecutor

import time, random, arrow, threading, uuid

import requests, queue, traceback, json, pymongo

# 链接mongodb
myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
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
    proxies = nike.getProxies()
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

    return True


# 修改设置
def updateSetting(index, user):
    global NUM

    try:
        msg("线程启动", "成功", "第 " + str(index) + " 次")

        msg('获取用户', user['phone'], user['name'])

        if not user['address']:
            msg('用户地址为空', '进入修改流程')
            driver = open()
            do_log = login(driver, user['phone'])
            if not do_log:
                return False

            address = nike.setAddress(driver, user['phone'])
            if not address:
                return False
            user['refresh_token'] = nike.getRefreshToken(driver, user['phone'])
            if not user['refresh_token']:
                return False

        proxies = nike.getProxies()

        access_token = nike.getAccessToken(user['phone'], user['refresh_token'], proxies)
        if not access_token:
            return False

        getSetting = nike.getSetting(access_token, proxies)
        if not getSetting:
            return False

        setSetting = nike.setSetttingApi(user['phone'], getSetting, access_token, proxies)
        if not setSetting:
            return False

        NUM += 1

        msg('成功统计', '数量', NUM)

        return True
    except:
        traceback.print_exc()
    finally:
        driver.quit()

    return True


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
def randomMouse(driver):
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

    msg('鼠标曲线移动移动')

    return True


# 登录
def login(driver, phone):
    num = 1
    while num <= 3:
        try:
            msg("用户登陆", '等待', phone)

            timeout = 30

            try:
                url = 'https://www.nike.com/cn/'
                driver.get(url)
            except:
                msg('访问NIKE首页', '代理访问超时')

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

            # 等待登录完成
            xpath = "//*[@id='ciclp-app']"
            WebDriverWait(driver, timeout, 0.5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )

            msg("用户登陆", '成功', phone)

            time.sleep(5)

            return driver
        except:
            traceback.print_exc()
            driver.save_screenshot(phone + '_' + str(arrow.now().timestamp) + '.png')
            num += 1
            continue

    return False


def msg(name, status='', content='', line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    start_time = arrow.now().timestamp

    # user = db_account.find().limit(100)
    user = db_account.find({'step': 'access_token'})

    # 线程索引
    threading_index = 1
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i in user:
            # future1 = pool.submit(train, threading_index, i)
            future1 = pool.submit(updateSetting, threading_index, i)
            threading_index += 1

    end_time = arrow.now().timestamp
    use_time = end_time - start_time

    time_msg = '总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))

    msg('时间统计', time_msg, "")

    msg("运行统计", "成功", NUM)
    msg("运行统计", "失败", threading_index - NUM)
