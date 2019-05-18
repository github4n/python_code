from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests as req
from PIL import Image
from io import BytesIO

import common.function as myFunc
import common.conf as conf
import time, pymongo, arrow, pymysql, hashlib

# 连接mongodb
myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
mydb = myclient["du"]

db_price = mydb["price"]
db_change = mydb["change"]

database = {
    "host": '144.48.9.105',
    "port": 3306,
    "user": 'rank666_com',
    "passwd": 'RdPK775JrWY3Psnb',
    "db": 'rank666_com',
    "charset": 'utf8',
}

db = pymysql.connect(host=database['host'], port=database['port'],
                     user=database['user'], password=database['passwd'],
                     db=database['db'], charset='utf8')
cursor = db.cursor(cursor=pymysql.cursors.DictCursor)


# 获取需要修改价格的列表
def getChange(user_id):
    where = {
        'user_id': user_id,
    }
    sql = myFunc.selectSql(conf.TABLE['taobao'], where)
    cursor.execute(sql)
    change_list = cursor.fetchall()

    while True:
        if not change_list:
            msg("获取改价列表", "列表为空", "30 秒后重新获取")
            time.sleep(30)
            continue
        break

    list = []
    for v in change_list:
        list.append(v)

    return list


def edit(driver, change_info):
    # 跳转商品编辑页面
    driver.get('https://item.publish.taobao.com/sell/publish.htm?itemId=' + str(change_info['taobao_id']))

    # 判断宝贝是否还存在
    is_have = driver.find_elements_by_xpath("//div[@class='feedback-notice-hd']")
    if is_have:
        msg("宝贝判断", "不存在", "请从改价列表中删除 淘宝ID：" + str(change_info['taobao_id']))
        return False

    # 获取鞋子价格
    ret_price = db_price.find({
        'articleNumber': change_info['article_number'],
    }, {'size', 'price'})

    if not ret_price:
        msg("获取毒的价格", "数据为空", "跳过货号" + str(change_info['article_number']))
        return False

    # 重构鞋子价格数组
    price_list = {}
    for v in ret_price:
        size = str(v['size']).replace('.0', '')
        price = str(v['price'] / 100).replace('.0', '')
        price_list[size] = price

    num = 0
    price_log = []

    goods_no_list = driver.find_elements_by_xpath("//div[@class='stretch']/table/tbody/tr/td[1]/div/div/p")
    for v in goods_no_list:
        goods_no_name = v.get_attribute('title')
        # 判断货号是否存在于这个里面
        if str(change_info['article_number']) not in str(goods_no_name):
            num += 1
            continue


        size = driver.find_elements_by_xpath("//div[@class='stretch']/table/tbody/tr/td[2]/div/div/p")[num].text
        dom_size = str(size)
        # 判断尺码在修改黑名单列表里 则跳过
        if change_info['size_list']:
            if dom_size in change_info['size_list']:
                num += 1
                continue


        # 判断尺码价格是否有价格
        if dom_size not in price_list:
            msg("获取毒的尺码价格", "数据为空", "跳过尺码：" + dom_size, False)
            num += 1
            continue


        # 获取原价格
        old_price = driver.find_elements_by_xpath("//input[@name='skuPrice']")[num].get_attribute('value')

        # 清除 input 的值
        driver.find_elements_by_xpath("//input[@name='skuPrice']")[num].clear()

        # 填写最新价格
        new_price = int(price_list[dom_size]) + int(change_info['price'])
        driver.find_elements_by_xpath("//input[@name='skuPrice']")[num].send_keys(new_price)

        # 记录价格变动修改
        edit_log = str(old_price) + ' ▶▶▶▶ ' + str(new_price) + "  尺码：" + str(dom_size)
        price_log.append(edit_log)

        num += 1

    # 通过聚焦使用 阿里自带 JS 修改一口价
    js = "document.getElementById('price').focus()"
    driver.execute_script(js)

    # 提交表单
    driver.find_elements_by_xpath("//button[@id='button-submit']")[0].click()

    # 监听是否有错误
    submit_error = driver.find_elements_by_xpath("//div[@class='sell-error-board ']/ul/li[1]")
    if not submit_error:
        msg("确认提交修改信息", "成功", "成功")
    else:
        submit_error = submit_error[0].text
        msg("确认提交修改信息", "失败", submit_error)

    # 等待 修改成功后跳转到 宝贝页面
    WebDriverWait(driver, 20, 0.5).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="J_Title"]'))
    )

    for v in price_log:
        msg("价格变动", "成功", v, False)

    return True


def startChrom():
    # 加启动配置
    option = webdriver.ChromeOptions()
    # 隐藏 "谷歌正在受到自动测试"
    option.add_argument('disable-infobars')

    # 不加载图片, 提升速度
    option.add_argument('blink-settings=imagesEnabled=false')
    # 后台运行
    # option.add_argument('headless')
    # 关闭console的信息输出
    option.add_argument('log-level=3')
    driver = webdriver.Chrome(executable_path='./driver/chromedriver_70_0_3538_16.exe', chrome_options=option)

    while True:
        try:
            # 淘宝出售中的宝贝
            url = 'https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Fsell.taobao.com%2Fauction%2Fgoods%2Fgoods_on_sale.htm%3Fspm%3Da21bo.2017.1997525073.4.5af911d96XwPw7'
            driver.get(url)

            msg('扫码登录', "等待", "请在 60秒 内， 扫描二维码登录！ 如果二维码超时，请重启程序！")

            # 等待 二维码
            qrcode = WebDriverWait(driver, 30, 0.5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="J_QRCodeImg"]/img'))
                , message="获取二维码失败，请重启程序！")

            # 文件显示手机扫码的二维码
            qrcode_src = qrcode.get_attribute('src')
            response = req.get(qrcode_src)
            image = Image.open(BytesIO(response.content))
            image.show()

            # 等待 登录成功
            WebDriverWait(driver, 60, 0.5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='多个ID以逗号或空格分隔']"))
                , message="登录超时，请重启程序，重新登录！")

            msg('扫码登录', "成功", "开始批量修改宝贝价格")

            break
        except:
            print("登录失败或超时，请重新扫码登录！")
            continue

    # 页面刷新时间  5分钟
    time_refresh = 0
    time_refresh_set = 5
    # 价格修改时间 10分钟
    time_edit = 600
    time_edit_set = 10
    while True:

        # 刷新页面 保持登录状态
        if time_refresh >= (60 * time_refresh_set):
            driver.refresh()
            time_refresh = 0

        # 修改价格
        if time_edit >= (60 * time_edit_set):
            change_list = getChange(4)
            for v in change_list:
                msg("修改价格", "开始", v['article_number'] + ' ' + v['title'])
                edit(driver, v)
            time_edit = 0

            next_time = arrow.now().timestamp + (60 * time_edit_set)
            next_time_str = arrow.get(next_time).to('local').format('YYYY-MM-DD HH:mm:ss')
            msg("批量修改", "成功", "下次启动时间：" + str(next_time_str))

        time.sleep(1)
        time_refresh += 1
        time_edit += 1


def msg(name, status, content, line=True):
    msg_time = arrow.get(arrow.now().timestamp).format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    startChrom()
