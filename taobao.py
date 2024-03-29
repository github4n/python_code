from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests as req
from PIL import Image
from io import BytesIO

import common.function as myFunc
import common.conf as conf
import time, pymongo, arrow, pymysql, hashlib, traceback

database = {
    "host": '144.48.9.105',
    "port": 3306,
    "user": 'rank666_com',
    "passwd": 'RdPK775JrWY3Psnb',
    "db": 'rank666_com',
    "charset": 'utf8',
}


def rankLogin():
    while True:
        try:
            db = pymysql.connect(host=database['host'], port=database['port'],
                                 user=database['user'], password=database['passwd'],
                                 db=database['db'], charset='utf8')
            cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
            break
        except:
            traceback.print_exc()
            print("数据连接超时，正在重连...")
            time.sleep(5)
            continue

    username = ''
    password = ''
    password_num = 1
    while True:
        if not username:
            username = input('请输入在RANK网站注册的用户名:')

        where = {
            'username': username,
        }
        sql = myFunc.selectSql(conf.TABLE['user'], where, ['id', 'password'])
        cursor.execute(sql)
        ret_user = cursor.fetchone()

        if not ret_user:
            print("账号：", username, "不存在", "请先去 http://www.rank666.com/index/user/login.html 注册")
            username = ''
            continue

        if not password:
            password = input('请输入账号：' + username + ' 的密码:')

        # MD5加密密码
        # 生成一个md5对象
        m1 = hashlib.md5()
        # 使用md5对象里的update方法md5转换
        m1.update(password.encode("GBK"))
        password = m1.hexdigest()

        # 判断账号密码是否成功
        if str(password) != str(ret_user['password']):
            print("密码不正确，请重新输入")
            password = ''
            if password_num >= 3:
                print("密码输入错误次数3次，请重新登录！")
                username = ''
                password_num = 1
            password_num += 1
            continue

        # 判断是否过期
        where = {
            'user_id': ret_user['id']
        }
        sql = myFunc.selectSql(conf.TABLE['function'], where, ['expire_time'])
        cursor.execute(sql)
        ret_expire = cursor.fetchone()

        if not ret_expire:
            print("账号：", username, "  还未开通，请先开通功能！")
            username = ''
            password = ''
            continue

        expire_time = arrow.get(str(ret_expire['expire_time'])).format('YYYY-MM-DD HH:mm:ss')
        if arrow.now().timestamp > ret_expire['expire_time']:
            print("账号已在 ", expire_time, '过期', " 请续费！")
            username = ''
            password = ''
            continue

        print("登录成功！", "账号过期时间：", expire_time)
        return ret_user['id']


# 获取需要修改价格的列表
def getChange(user_id):
    mysql_num = 1
    while mysql_num <= 3:
        try:
            db = pymysql.connect(host=database['host'], port=database['port'],
                                 user=database['user'], password=database['passwd'],
                                 db=database['db'], charset='utf8')
            cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
            break
        except:
            msg("脚本初始化", "失败", "正在重置 第 " + str(mysql_num) + " 次")
            time.sleep(5)
            mysql_num += 1
            continue

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


def edit(driver, change_info, myclient):
    try:
        mydb = myclient["du"]
        db_price = mydb["price"]

        # 跳转之前判断是否有表单弹窗
        result = EC.alert_is_present()(driver)
        if result:
            result.accept()
            msg('弹框点击', '成功', '确认离开该页面！')


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

        price_log_yes = {}
        price_log_no = {}

        # 一口价
        yikou_price = {}

        # 是否修改
        is_edit = 0

        for i in range(1, 10):
            time.sleep(0.5)

            index = 0

            # 价格节点
            xpath_str1 = "//td[@class='sell-sku-cell sell-sku-cell-money']/div/span/span/span/input"
            dom_size_list = driver.find_elements_by_xpath(xpath_str1)
            # 货号节点
            xpath_str2 = "//tr[@class='sku-table-row']/td[1]/div/div/p"
            goods_no_list = driver.find_elements_by_xpath(xpath_str2)

            # 尺码节点
            xpath_str3 = "//tr[@class='sku-table-row']/td[2]/div/div/p"
            size_list = driver.find_elements_by_xpath(xpath_str3)

            # 销量节点
            xpath_str4 = "//tr[@class='sku-table-row']/td[4]/div/span/span/span/input"
            sold_list = driver.find_elements_by_xpath(xpath_str4)

            for v in dom_size_list:
                # 价格
                old_price = v.get_attribute('value')
                old_price = int(old_price.replace('.00', ''))
                # 货号
                goods_no = goods_no_list[index].get_attribute('title')
                # 尺码
                size = size_list[index].get_attribute('title')
                dom_size = str(size)
                # 销量
                sold = sold_list[index].get_attribute('value')

                # 记录一口价
                if int(sold) > 0:
                    yikou_price[goods_no + size] = old_price

                # 判断货号一致性
                if change_info['article_number'] not in goods_no:
                    # msg("货号判断：", '目标货号：' + change_info['article_number'], "淘宝sku名称：", goods_no)
                    index += 1
                    continue

                # 判断尺码在修改黑名单列表里 则跳过
                if change_info['size_list']:
                    if dom_size in change_info['size_list']:
                        index += 1
                        continue

                # 判断尺码价格是否有价格
                if dom_size not in price_list:
                    # msg("获取尺码价格", "没有毒数据", "跳过尺码：" + dom_size, False)
                    index += 1
                    continue


                # 获取最新价格
                new_price = int(price_list[dom_size]) + int(change_info['price'])

                # 只有价格不相等才修改
                if int(old_price) != int(new_price):
                    # 清除 input 的值
                    v.clear()
                    v.send_keys(new_price)

                    # 修改状态 + 1
                    is_edit += 1

                    edit_log = "毒：" + str(price_list[dom_size]) + " " + str(change_info['price']) + "  " + str(
                        old_price) + ' ▶▶▶▶ ' + str(
                        new_price) + "  尺码：" + str(dom_size)
                    price_log_yes[dom_size] = edit_log

                else:
                    edit_log = "毒：" + str(price_list[dom_size]) + " " + str(change_info['price']) + "  " + str(
                        old_price) + ' ▶▶▶▶ ' + str(
                        new_price) + "  尺码：" + str(dom_size)
                    # 记录价格变动修改
                    price_log_no[dom_size] = edit_log





                # 通过聚焦使用 阿里自带 JS 修改一口价
                js = "document.getElementById('price').focus()"
                driver.execute_script(js)



                # 记录一口价
                if int(sold) > 0:
                    price = v.get_attribute('value')
                    price = int(price.replace('.00', ''))
                    yikou_price[goods_no + size] = price

                index += 1


            # 滚动页面
            scrollTop = 40 + (i * 520)
            js = "document.getElementsByClassName('ver-scroll-wrap')[0].scrollTop=" + str(scrollTop)
            driver.execute_script(js)


        # 判断是否有价格变动信息 没有代表sku货号不存在
        if (not price_log_no) and (not price_log_yes):
            msg("价格变动", "失败", "请检查sku名称 是否添加了货号:" + change_info['article_number'])
            return False

        if price_log_yes:
            for k, v in price_log_yes.items():
                msg("价格变动", "修改", v, False)
            print("\n")

        if price_log_no:
            for k, v in price_log_no.items():
                msg("价格变动", "价格无变动，不修改", v, False)

        print("-----------------------------------------")


        # 填写一口价
        if not yikou_price:
            msg("填写一口价", "货号：" + str(change_info['article_number']), "所有库存为 0，不修改价格")
            return False


        # 获取老一口价价格
        yikou_old_price = driver.find_element_by_xpath("//input[@id='price']").get_attribute('value')
        yikou_old_price = int(yikou_old_price.replace('.00', ''))
        # 获取一口价
        min_price = int(min(yikou_price.values()))


        if yikou_old_price == min_price:
            msg("填写一口价", "货号：" + str(change_info['article_number']), "一口价没有变动 老：" + str(yikou_old_price) + ' 新：' + str(min_price))
        else:
            msg("填写一口价", "货号：" + str(change_info['article_number']), "设置一口价：" + str(min_price))
            # 重复填写一口价3次
            yikou_num = 1
            while yikou_num <= 3:
                driver.find_element_by_xpath("//input[@id='price']").clear()
                driver.find_element_by_xpath("//input[@id='price']").send_keys(min_price)
                yikou_num += 1

            WebDriverWait(driver, 20, 0.5).until(
                EC.presence_of_element_located((By.XPATH, "//button[@id='button-submit']"))
            )
            # 修改状态 + 1
            is_edit += 1

        # code_num = 1
        # while code_num <= 11:
        #     if code_num == 10:
        #         msg('等待手机验证码', '超时', '请重新执行脚本！')
        #         driver.close()
        #         driver.quit()
        #         quit()
        #         return False
        #
        #     # 检测是否需要发送手机验证码
        #     xpath = "//div[text()='发布商品验证']"
        #     code = driver.find_elements_by_xpath(xpath)
        #     if code:
        #         msg('等待手机验证码', '等待', '已等待 ' + str(code_num * 10) + ' 秒')
        #         time.sleep(10)
        #         code_num += 1
        #         continue
        #     else:
        #         break

        msg('修改条数统计', '数量：', is_edit)

        if is_edit == 0:
            msg('修改状态判断', '无修改', '最新价格没有变动，不修改该宝贝。')
            return False

        # 提交表单
        driver.find_element_by_xpath("//button[@id='button-submit']").click()

        # 监听是否有错误
        submit_error = driver.find_elements_by_xpath("//div[@class='sell-error-board ']/ul/li[1]")
        if not submit_error:
            msg("表单提交修改信息", "成功", "成功")
        else:
            submit_error = submit_error[0].text
            msg("表单提交修改信息", "失败", submit_error)


        time.sleep(1)

        # 防止没有提交成功 一直提交
        click_num = 1
        while click_num <= 5:
            try:
                # 等待 修改成功后跳转到 宝贝页面
                WebDriverWait(driver, 5, 0.5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="J_Title"]'))
                )
                break
            except:
                traceback.print_exc()
                msg("确认提交修改信息", "重试", "第" + str(click_num) + "次")
                time.sleep(1)
                # 提交按钮
                driver.find_element_by_xpath("//button[@id='button-submit']").click()

                click_num += 1



        return True
    except:
        traceback.print_exc()


def startChrom():
    # 账号登录
    user_id = rankLogin()
    # user_id = 4
    # user_id = 147

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

    # 淘宝出售中的宝贝
    url = 'https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Fsell.taobao.com%2Fauction%2Fgoods%2Fgoods_on_sale.htm%3Fspm%3Da21bo.2017.1997525073.4.5af911d96XwPw7'
    driver.get(url)

    i = 1
    while i <= 3:
        try:
            # 淘宝出售中的宝贝
            url = 'https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Fsell.taobao.com%2Fauction%2Fgoods%2Fgoods_on_sale.htm%3Fspm%3Da21bo.2017.1997525073.4.5af911d96XwPw7'
            driver.get(url)

            msg('扫码登录', "等待", "请在 60秒 内， 扫描二维码登录！")
            msg('扫码登录', "等待", "如果二维码超时，请重启程序！")
            msg('扫码登录', "等待", "登录后，关闭二维码图片才能执行程序！")

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
            i += 1
            time.sleep(1)
            continue

    # 页面刷新时间  5分钟
    time_refresh = 0
    time_refresh_set = 5
    # 价格修改时间 10分钟
    time_edit = 1200
    time_edit_set = 20
    while True:
        # 刷新页面 保持登录状态
        if time_refresh >= (60 * time_refresh_set):
            driver.refresh()
            time_refresh = 0

        # 修改价格
        if time_edit >= (60 * time_edit_set):
            change_list = getChange(user_id)

            # mongo重连
            mongo_num = 1
            while mongo_num <= 3:
                try:
                    # 连接mongodb
                    myclient = pymongo.MongoClient("mongodb://levislin:!!23Bayuesiri@144.48.9.105:27017")
                    break
                except:
                    print("初始化", "失败", "重连 " + str(mongo_num) + "次")
                    mongo_num += 1
                    time.sleep(5)
                    continue
            list_num = 0
            for v in change_list:
                if list_num == 50:
                    time.sleep(2*60)
                    msg('休眠2分钟，防止过多访问', 200, '宝贝数量修改达到 50 个，进入休眠状态')
                    list_num = 0

                msg("修改价格", "开始", v['article_number'] + ' ' + v['title'])
                edit(driver, v, myclient)
                list_num += 1

            time_edit = 0

            next_time = arrow.now().timestamp + (60 * time_edit_set)
            next_time_str = arrow.get(next_time).to('local').format('YYYY-MM-DD HH:mm:ss')
            msg("批量修改", "成功", "下次启动时间：" + str(next_time_str))

        time.sleep(1)
        time_refresh += 1
        time_edit += 1


def msg(name, status, content, line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    print('--------------------------------')
    print('          RANK 淘宝改价          ')
    print('          version 1.2           ')
    print('--------------------------------')
    print('更新说明                         ')
    print('1.只修改价格有变动尺码             ')
    print('2.只修改有变动一口价              ')
    print('2.每改50个宝贝会休眠2分钟，防止禁止修改')
    print('--------------------------------')

    startChrom()
