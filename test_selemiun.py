from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import time

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests

PROXIES_API = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=6&sb=0&pb=4&mr=1&regions='


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
# 后台运行
# option.add_argument('headless')
# 开启实验性功能参数
# option.add_experimental_option('excludeSwitches', ['enable-automation'])

# driver = webdriver.Chrome(executable_path='./driver/chromedriver_74.exe', desired_capabilities=capabilities,
#                           chrome_options=option)
driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe', chrome_options=option)

# 隐式等待
driver.implicitly_wait(2)

driver.get('http://rank666.com/index/index/captcha2')
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