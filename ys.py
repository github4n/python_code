import ys_bypass as bp
import time
import arrow, random
import requests
from bs4 import BeautifulSoup
import json, threading, traceback
from multiprocessing import Pool, Queue

''' 初始设置 '''
# 设置要购买的鞋子名称
SEARCH_NAME = 'flannel-lined-canvas-jacket-medium-blue'

# 设置购买尺码
buy_size = ['L', 'M']

# 访问延迟时间
PAY_DELAY = 1

# 设置超时时间
TIMEOUT = 5

# 设置并发线程数量
PAY_NUM = 20

''' 初始设置 '''

# 连接mongodb
mydb = bp.myclient["ys"]
mongo = bp.mydb["bypass"]
log = bp.mydb['log']
shoes = bp.mydb['shoes']

# 设置尺码列表
size_arr = {}

# pay 错误信息
pay_error = {
    'Card was declined': '卡被拒绝了',
    'CARD WAS DECLINED': '信用卡额度不足',
    'Your card was declined': '您的信用卡遭到拒绝',
    'Street address and postal code do not match.': '街道地址和邮政编码不匹配。',
    'This transaction has been declined': '本次交易已被拒绝',
    'This transaction cannot be processed.': '此交易无法处理。',
    'There was a problem processing the payment. Try a different payment method or try again later.': '处理付款时出现问题。尝试其他付款方式或稍后再试。',
    'No Match': '不匹配',
    'Some items are no longer available. Your cart has been updated.': '有些商品不再可用。你的购物车已经更新。',
}

# bypass 消息队列
BYPASS_LIST = Queue(maxsize=1000)

# ip全局储存列表
IP_LIST = []

''' 以下是抢购流程 '''


# 维持线程池
def proxiesPool():
    while True:
        # 获取ip组
        if len(IP_LIST) <= 30:
            proxies_url = 'http://webapi.http.zhimacangku.com/getip?num=200&type=2&pro=320000&city=0&yys=0&port=11&time=1&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=2&regions='
            ret = requests.get(proxies_url)
            if ret.status_code != 200:
                reqMsg('获取代理IP[组]', ret.status_code, '失败', ret.json())
                return False

            if ret.json()['code'] != 0:
                reqMsg('获取代理IP[组]', ret.json()['code'], '失败', ret.json()['msg'])
                return False

            for v in ret.json()['data']:
                ip = {
                    'https': 'https://' + str(v['ip']) + ':' + str(v['port'])
                }
                IP_LIST.append(ip)

            reqMsg('获取代理IP[组]', ret.status_code, '成功', "获取ip数量：" + str(len(IP_LIST)))
        else:
            time.sleep(1)
            continue


# 获取代理ip
def getProxies():
    while True:
        # 获取一个ip
        if len(IP_LIST) <= 10:
            reqMsg('等待获取代理IP', 200, '等待', '等待')
            time.sleep(0.5)
            continue
        else:
            ip = IP_LIST.pop()
            reqMsg('获取代理IP', 200, '成功', ip)

            return ip


# 测试代理是否成功
def testProxies(req, name):
    while True:
        try:
            ret = req.get('https://icanhazip.com')
            if ret.status_code != 200:
                continue

            reqMsg(name + " ip:", ret.status_code, '成功', ret.text)
            return
        except:
            continue


# 添加商品
def cartAdd(req, goods_id, cookies, auth_token):
    name = '支付-添加商品'
    num = 0
    while True:
        try:
            params_json = {
                "id": goods_id,
                "quantity": 1,
                "properties": {}
            }

            cart_add = req.post(bp.URL['add'], json=params_json, headers=bp.HEADERS, cookies=cookies, timeout=TIMEOUT)
            if cart_add.status_code != 200:
                reqMsg(name, cart_add.status_code, '接口返回非200', cart_add.json)
                # 重新获取 ip 在重试
                req.proxies.update(getProxies())

                continue

            total_price = cart_add.json()['price']
            total_price = total_price.replace('.', '')

            reqMsg(name, cart_add.status_code, '成功', total_price)

            return total_price
        except:
            # 重新获取 ip 在重试
            req.proxies.update(getProxies())

            num += 1
            traceback.print_exc()
            reqMsg(name, 503, auth_token + ' 接口异常', '切换IP, 重连 ' + str(num) + ' 次')
            # time.sleep(PAY_DELAY)
            continue


# 获取购物车
def cartGet(req, cookies, auth_token):
    name = '支付-获取购物车'
    num = 0
    while True:
        try:
            params_json = {
                'updates[]': 1,
                'checkout': 'CHECKOUT'
            }
            cart_get = req.post(bp.URL['cart'], json=params_json, headers=bp.HEADERS, cookies=cookies, timeout=TIMEOUT)
            if (cart_get.status_code != 200):
                reqMsg(name, cart_get.status_code, '接口返回非200', cart_get.text)
                # 重新获取 ip 在重试
                req.proxies.update(getProxies())
                continue

            # 判断购物车是否为空
            assert bp.checkCart(cart_get.text)

            reqMsg(name, cart_get.status_code, '成功', cart_get.text)
            return cart_get.text
        except:
            # 重新获取 ip 在重试
            req.proxies.update(getProxies())

            num += 1
            traceback.print_exc()
            reqMsg(name, 503, auth_token + ' 接口异常', '切换IP, 重连 ' + str(num) + ' 次')
            # time.sleep(PAY_DELAY)
            continue


# 获取支付令牌
def getPaymentToken(req, auth_token):
    num = 0
    while True:
        try:
            reqMsg("开始获取支付token", 200, "成功", "请等待")

            params_json = {
                "credit_card": {
                    "number": '370288903123969',  # 去掉空格
                    "name": '林文强',
                    "month": '4',  # 单位数去掉0
                    "year": '2024',
                    "verification_value": '507'
                }
            }

            ret = req.post(bp.URL['credit'], json=params_json, headers=bp.HEADERS, timeout=TIMEOUT)
            if ret.status_code != 200:
                reqMsg("获取支付token", ret.status_code, "获取失败 " + auth_token, ret.text)
                # 重新获取 ip 在重试
                req.proxies.update(getProxies())
                continue

            reqMsg("获取支付token", 200, "成功", ret.text)

            payment_token = json.loads(ret.text)["id"]

            return payment_token
        except:
            # 重新获取 ip 在重试
            req.proxies.update(getProxies())

            num += 1
            reqMsg('获取支付token', 503, ' 接口异常 ' + auth_token, '切换IP, 重连 ' + str(num) + ' 次')
            time.sleep(PAY_DELAY)
            continue


# 查找商品
def search():
    ''' 无限访问首页直到没有  302重定向 或 失败为止 '''
    num_302 = 0  # 302 重定向重试次数
    num_fail = 0  # 访问失败重试次数
    replay_ip = {}
    num = 1
    # 重试 5 次后切换IP
    try_num = 10
    while True:
        try:
            # 访问网站获取Dom
            ret = requests.get(bp.URL['product'] + SEARCH_NAME, allow_redirects=False, timeout=5, proxies=replay_ip)
            # 判断页面是否重定向
            if (ret.status_code == 302):
                if num >= try_num:
                    num = 1
                    # 重新获取 ip 在重试
                    replay_ip = getProxies()

                num += 1
                num_302 += 1
                reqMsg('搜索商品-访问首页', ret.status_code, '页面重定向 302 重连次数：' + str(num_302), '页面重定向 302')
                time.sleep(1)
                continue

            if (ret.status_code != 200 and ret.status_code != 302):
                if num >= try_num:
                    num = 1
                    # 重新获取 ip 在重试
                    replay_ip = getProxies()

                num += 1

                num_fail += 1
                reqMsg('搜索商品-访问首页', ret.status_code, '访问失败 重连次数：' + str(num_fail), ret.text)
                time.sleep(1)
                continue

            reqMsg('搜索商品-访问首页', ret.status_code, '成功 302次数：' + str(num_302) + ' 失败重连：' + str(num_fail), ret.text)
            break
        except:
            # 重新获取 ip 在重试
            replay_ip = getProxies()

            num += 1

            reqMsg('搜索商品-访问首页', 503, '接口异常', '切换IP,  正在重连...')
            time.sleep(1)
            continue

    # 判断Dom是否存在
    soup = BeautifulSoup(ret.text, "html.parser")
    dom_id = 'js-product-json'
    script_content = soup.find(class_=dom_id)
    if script_content is None:
        reqMsg('搜索商品-查找储存json数据的Dom', 404, '找不到 Dom：class=js-product-json', script_content)
        return False

    # 获取 script 里的 json 字符串转换成 字典
    script_content = script_content.get_text()
    product = json.loads(script_content)

    # 获取尺码列表
    size_list = product['variants']
    if not size_list:
        reqMsg('搜索商品-判断尺码列表是否为空', 404, '当前尺码列表 variants 为空', size_list)
        return False

    # 获取可用尺码
    for v in size_list:
        if v['available'] == True:
            size_arr[v['options'][0]] = v['id']

    if not size_arr:
        reqMsg('搜索商品-查找可用尺码', 404, '当前可用 为空', size_list)

    # 清空集合
    shoes.delete_many(
        {'time': {'$lt': arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')}})

    # 遍历插入数据库以待使用
    for k, v in size_arr.items():
        data = {
            'title': product['title'],
            'size': k,
            'id': v,
            'status': 1,
            'image': product['featured_image'],
            'time': arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'),
        }
        shoes.insert_one(data)

    reqMsg('搜索商品-插入搜索到的尺码ID', 200, '成功', size_arr)


# 获取购买尺码，按照数组前后设置优先级
def getSize():
    while True:
        # 查询尺码是否还有库存
        for v in buy_size:
            where = {
                'status': 1,
                'size': v
            }
            ret = shoes.find_one(where)
            if ret:
                return {'size': ret['size'], 'id': ret['id']}
            else:
                print("等待获取尺码")
                continue
                time.sleep(0.5)


def setBypass():
    ret_bypass = mongo.find({'pay': 0, 'error': 0, 'get': 0})
    for v in ret_bypass:
        BYPASS_LIST.put(v)


# 抢购开始
def start():
    # 获取尺码ID
    size_arr = getSize()

    # 获取一个未付款的 bypass
    while True:
        if not BYPASS_LIST.empty():
            bypass = BYPASS_LIST.get()
            if not bypass:
                reqMsg("没有BYPASS了", 404, '没有BYPASS了', '没有BYPASS了')
                return False
            break
        else:
            time.sleep(1)
            continue

    # 设置 request 对象
    req = requests.session()

    # 设置 芝麻代理 ip
    req.proxies.update(getProxies())

    # 添加要购买的商品
    total_price = cartAdd(req, size_arr['id'], bypass['cookies'], bypass['auth_token'])
    if not total_price:
        return False

    # 刷新购物车
    ret = cartGet(req, bypass['cookies'], bypass['auth_token'])
    if not ret:
        return False

    # # 获取支付令牌
    payment_token = getPaymentToken(req, bypass['auth_token'])

    pay(req, bypass, total_price, payment_token, size_arr['size'])


# 付款
def pay(req, bypass, total_price, payment_token, size):
    reqMsg('正在发起付款请求：', 200, '成功', '请等待')

    # 付款要传的数据
    data = {
        "utf8": u"\u2713",
        "_method": "patch",
        "authenticity_token": bypass['auth_token'],
        "previous_step": "payment_method",
        "step": "",
        "s": payment_token,
        "checkout[payment_gateway]": bp.gateway,
        "checkout[credit_card][vault]": "false",
        "checkout[different_billing_address]": "false",
        "checkout[total_price]": total_price,
        "complete": "1",
        "checkout[client_details][browser_width]": str(random.randint(1000, 2000)),
        "checkout[client_details][browser_height]": str(random.randint(1000, 2000)),
        "checkout[client_details][javascript_enabled]": "1",
    }
    # 总价：payment-due__price
    # 付款：notice notice--error

    # 重新代理ip
    num = 0
    while True:
        try:
            ret = req.post(bypass['payment_url'], data=data, headers=bp.HEADERS, timeout=5)
            if (ret.status_code != 200):
                reqMsg('付款请求', ret.status_code, '接口返回非200', ret.text)
                return False
            else:
                reqMsg('付款请求', ret.status_code, '成功', data)
                break
        except:
            # 重新获取 ip 在重试
            req.proxies.update(getProxies())

            num += 1
            reqMsg('付款请求', 503, ' 接口异常 ' + bypass['auth_token'], '切换IP,  重连 ' + str(num) + ' 次')
            continue

    # 判断付款是否成功
    ret_pay = getPayError(ret.text, bypass['auth_token'])
    if ret_pay == True:
        reqMsg('付款', 200, '成功', '成功')
        # 修改支付状态
        where = {'auth_token': bypass['auth_token']}
        ret_edit = mongo.update_one(where, {'$set': {
            'size': size,
            'pay': 1,
        }})
        if ret_edit.modified_count == 1:
            reqMsg('付款状态修改-成功', 200, '成功', {
                'auth_token': bypass['auth_token'],
                'size': size,
                'pay': 1,
            })
        else:
            reqMsg('付款状态修改-成功', 503, '失败', {
                'auth_token': bypass['auth_token'],
                'size': size,
                'pay': 1,
            })
            return False

        return True
    else:
        reqMsg('付款：', 503, '失败 ' + bypass['auth_token'], ret_pay)
        # 修改支付状态
        where = {'payment_url': bypass['payment_url']}
        ret_edit = mongo.update_one(where, {'$set': {
            'size': size,
            'error': ret_pay,
        }})
        if ret_edit.modified_count == 1:
            reqMsg('付款状态修改-失败', 200, '成功', {
                'auth_token': bypass['auth_token'],
                'size': size,
                'error': ret_pay,
            })
        else:
            reqMsg('付款状态修改-失败', 503, '失败', {
                'auth_token': bypass['auth_token'],
                'size': size,
                'error': ret_pay,
            })
            return False

        return False


# 获取支付错误信息
def getPayError(dom, auth_token):
    soup = BeautifulSoup(dom, 'html.parser')
    error = soup.find('p', class_="notice__text")
    if error is None:
        return True

    error = error.get_text()

    # 输出中文付款错误
    for k, v in pay_error.items():
        if error in k:
            error = v

    reqMsg("支付错误信息", 503, error, auth_token)

    return error


# 检测是不是访问过多
def check429(ret, name):
    if ret.status_code == 429:
        reqMsg(name, ret.status_code, '访问次数过多', '访问次数过多')
        return False
    return True


# 信息输出
def reqMsg(name, code, msg, content):
    print('[步骤]：', name, end='\n')
    print('[状态]：', code, end='\n')
    print('[说明]：', msg, end='\n')
    if (len(str(content)) > 200):
        print('[内容]：', len(str(content)), end='\n')
    else:
        print('[内容]：', content, end='\n')
    print('---------------------------------------------------', end='\n')

    now_time = arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')

    # 记录log
    log_info = {
        # '名称':goods,
        # '尺码':size,
        '步骤': name,
        '状态': code,
        '说明': msg,
        '内容': content,
        '时间': now_time,
    }
    bp.pay_log.insert_one(log_info)


# 开启线程
def threadPay(pro_num, num=0):
    # 生成bp
    task_number = PAY_NUM

    if num != 0:
        task_number = num

    i = 1
    tasks = []

    # 开启 ip池线程
    t_ip = threading.Thread(target=proxiesPool)
    t_ip.start()

    # 开启 鞋子尺码维护池
    t_shoes = threading.Thread(target=search)
    t_shoes.start()

    while i <= task_number:
        reqMsg('开启 第 ' + str(pro_num) + " 个进程 " + " 第 " + str(num) + " 线程", 200, '成功', '成功')

        # 开启线程
        t = threading.Thread(target=start)
        tasks.append(t)
        t.start()

        i += 1


if __name__ == "__main__":



    # 开启多线程 付款
    p = Pool(10)

    # 获取bypass
    p.apply_async(setBypass)
    for i in range(2):
        p.apply_async(threadPay, args=(i, 10))

    p.close()
    p.join()
