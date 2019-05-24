import ys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import common.phone as phoneSdk
import common.randName as nameSdk
import time,random

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests

PROXIES_API = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=6&sb=0&pb=4&mr=1&regions='


def login():
    login_dom = "//li[@class='member-nav-item has-submenu d-sm-ib va-sm-m']/div"

    myaccount_dom = "//div[@id='AccountNavigationDropdown']"
    is_show = driver.find_element_by_xpath(myaccount_dom).is_displayed()
    print(is_show)

    # 点击显示登录框
    driver.find_element_by_xpath(login_dom).click()

    # 输入手机号
    dom_phone = "//input[@placeholder='手机号码']"
    driver.find_element_by_xpath(dom_phone).send_keys('18968804688')

    # 输入密码
    dom_phone = "//input[@placeholder='密码']"
    driver.find_element_by_xpath(dom_phone).send_keys('Mn476489634')

    # 点击登录
    login_dom = "//input[@value='登录']"
    driver.find_element_by_xpath(login_dom).click()

    # 判断是否登录
    check_num = 1
    while check_num <= 5:
        time.sleep(5)

        is_show = driver.find_element_by_xpath(myaccount_dom).is_displayed()
        if not is_show:
            print("正在检测登录状态", "第 " + str(check_num) + " 次")
            check_num += 1
            continue
        print("登录成功")
        break

    # 跳转需要抽奖的鞋子
    url = 'https://www.nike.com/cn/launch/t/'
    name = 'air-max-tailwind-4-digi-camo'
    url = url + name

    driver.get(url)

    time.sleep(10)
    # 点击抽奖
    js = "document.getElementsByClassName('buying-tools-container').firstChild.click()"
    driver.execute_script(js)

# 获取代理ip
def getProxies():
    ret = requests.get(PROXIES_API)
    if ret.status_code != 200:
        print('获取代理IP', ret.status_code, '获取代理ip失败', ret.text)

    print('获取代理IP', ret.status_code, '成功', ret.text)

    return ret.text


capabilities = dict(DesiredCapabilities.CHROME)
# capabilities['proxy'] = {'proxyType': 'MANUAL',
#                          'httpProxy': getProxies(),
#                          'class': "org.openqa.selenium.Proxy",
#                          'autodetect': False}

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

# driver = webdriver.Chrome(executable_path='./driver/chromedriver_74.exe', desired_capabilities=capabilities,
#                           chrome_options=option)
driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe', chrome_options=option)
# 窗口最大化
driver.maximize_window()


# 隐式等待
driver.implicitly_wait(2)

driver.get('https://www.nike.com/cn/zh_cn/s/register')

time.sleep(0.5)
# 点击立即加入
xpath = "//a[text()='立即加入。']"
driver.find_element_by_xpath(xpath).click()



# 获取手机号
phone = phoneSdk.Phone.getPhone(723)

# 填写手机号
xpath = "//input[@placeholder='手机号码']"
driver.find_element_by_xpath(xpath).send_keys(phone)

# 点击发送验证码
xpath = "//input[@value='发送验证码']"
driver.find_element_by_xpath(xpath).click()

sms_num = 1
while sms_num <= 3:
    # 等待获取验证码
    sms = phoneSdk.Phone.getSms(phone, 723)
    if not sms:
        print("【获取验证码】超时", "第 " + str(sms_num) + " 次")
        # 点击发送验证码
        driver.find_element_by_xpath(xpath).click()
        continue
    break

# 填写验证码
xpath = "//input[@placeholder='输入验证码']"
driver.find_element_by_xpath(xpath).send_keys(sms)


# 点击 继续
xpath = "//input[@value='继续']"
driver.find_element_by_xpath(xpath).click()


# 获取姓名
name = nameSdk.getName()

# 填写 姓
xpath = "//input[@placeholder='姓氏']"
driver.find_element_by_xpath(xpath).send_keys(name['xm'])

# 填写 名
xpath = "//input[@placeholder='名字']"
driver.find_element_by_xpath(xpath).send_keys(name['mz'])

# 填写 密码
xpath = "//input[@placeholder='密码']"
driver.find_element_by_xpath(xpath).send_keys('Mn476489634')

# 选择 性别 男 M
xpath = "//ul[@data-componentname='gender']/li"
driver.find_elements_by_xpath(xpath)[0].click()

# 点击注册
xpath = "//input[@value='注册']"
driver.find_element_by_xpath(xpath).click()


time.sleep(5)
# 点击跳过 这样才能登陆
xpath = "//input[@value='跳过']"
driver.find_element_by_xpath(xpath).click()

# 跳转地址设置
driver.get("https://www.nike.com/member/settings/addresses")

time.sleep(5)
# 点击添加配送地址
xpath = "//*[@class='ncss-btn-secondary-dark d-sm-h d-md-ib']"
driver.find_elements_by_xpath(xpath)[2].click()

# 设置默认配送地址
xpath = "//*[text()='将其设为我的默认配送地址']"
driver.find_element_by_xpath(xpath).click()

# 填写 姓
xpath = "//input[@name='姓氏']"
driver.find_element_by_xpath(xpath).send_keys(name['xm'])
time.sleep(1)
driver.find_element_by_xpath(xpath).clear()
driver.find_element_by_xpath(xpath).send_keys(name['xm'])

# 填写 名
xpath = "//input[@name='名字']"
driver.find_element_by_xpath(xpath).send_keys(name['mz'])
time.sleep(0.5)
driver.find_element_by_xpath(xpath).clear()
driver.find_element_by_xpath(xpath).send_keys(name['mz'])

# 选择省份 江苏省
xpath = "//*[@id='省份']/option[@value='CN-32']"
driver.find_element_by_xpath(xpath).click()

# 选择城市 徐州市
xpath = "//*[@id='城市']/option[@value='徐州市']"
driver.find_element_by_xpath(xpath).click()

# 选择城市 徐州市
xpath = "//*[@id='乡镇区县']/option[@value='贾汪区']"
driver.find_element_by_xpath(xpath).click()

# 填写 地址一
address = ['大泉街道', '老矿街道', '工业园区管委会', '江庄街道']
address = random.choice(address)
address_random = nameSdk.getAddress()
address = address + address_random
print("【获取地址】：", address)

xpath = "//*[@id='地址 1']"
driver.find_element_by_xpath(xpath).send_keys(address)
time.sleep(0.5)
driver.find_element_by_xpath(xpath).clear()
driver.find_element_by_xpath(xpath).send_keys(address)

# 填写电话号码
xpath = "//*[@id='电话号码']"
driver.find_element_by_xpath(xpath).send_keys(phone)

# 点击保存
time.sleep(1)
xpath = "//*[text()='保存']"
driver.find_element_by_xpath(xpath).click()















# button_dom = "//div[@class='buying-tools-container']/button"
# element = WebDriverWait(driver, 10, 0.5).until(
#     EC.presence_of_element_located((By.XPATH, button_dom))
# )
# driver.find_element_by_xpath(button_dom).click()






# driver.get('http://www.baidu.com')

# element = WebDriverWait(driver, 10, 0.5).until(
#     EC.presence_of_element_located((By.CLASS_NAME, "recaptcha-checkbox-checkmark"))
# )
# iframe打开问题
# iframe = driver.find_elements_by_tag_name("iframe")[0]
# driver.switch_to_frame(iframe)
#
# # 对定位到的元素执行鼠标悬停操作
# # ActionChains(driver).move_to_element(iframe).perform()
# time.sleep(2)
# driver.find_element_by_xpath("//div[@class='recaptcha-checkbox-checkmark']").click()
#
#
# driver.switch_to_default_content()
#
#
# iframe2 = driver.find_elements_by_xpath("//iframe[starts-with(@name,'c-')]")[0]
# driver.switch_to_frame(iframe2)
# time.sleep(2)
# driver.find_element_by_xpath('//*[@id="recaptcha-audio-button"]').click()


# driver.quit()
