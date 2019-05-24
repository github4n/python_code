from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class driver():


    def open(self):
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

        return driver
