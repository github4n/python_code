import time

import arrow, random

import common.conf as conf
import requests, pymongo
from bs4 import BeautifulSoup
import json, asyncio

''' 初始设置 '''

# 开始加入购物车的id
goods_id = '707316285459'

# 设置购买尺码
buy_size = ['L', 'M']

# 设置gateway
gateway = '117647559'

# 访问延迟时间
delay = 1

# 设置超时时间
timeout = 60

''' 初始设置 '''

# 域名
host = 'https://yeezysupply.com/'
# 接口
URL = {
    'add': host + 'cart/add.json',
    'change': host + 'cart/change.json',
    'cart': host + 'cart',
    'bp': host + '17655971/checkouts/',
    'product': host + 'products/',
    'credit': "https://elb.deposit.shopifycs.com/sessions",
}

# 设置user-agent
user_agents = [
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5"
]
# 随机获取一个
user_agent = random.choice(user_agents)
# 设置头部
headers = {
    'User-Agent': user_agent
}
# 设置代理
proxies = {
    # 'http': 'http://lum-customer-hl_78c9691a-zone-zone1-country-us:ze86qxp2bgyp@zproxy.lum-superproxy.io:22225'
}

# 第一步：联系地址 订单的webForm
form_1 = {
    'utf8': u"\u2713",
    '_method': 'patch',
    'authenticity_token': '',  # 通过购物车Dom获取
    'previous_step': 'contact_information',
    'step': 'shipping_method',

    'checkout[email]': '515788423@qq.com',
    'checkout[buyer_accepts_marketing]': '0',

    'checkout[shipping_address][first_name]': 'KARL',
    'checkout[shipping_address][last_name]': 'CHENTAIYUAN',
    'checkout[shipping_address][address1]': '6215 NE 92nd Dr',
    'checkout[shipping_address][address2]': 'C/O YCH061',
    'checkout[shipping_address][city]': 'Portland',
    'checkout[shipping_address][country]': 'US',
    'checkout[shipping_address][province]': 'Oregon',
    'checkout[shipping_address][zip]': '97253',
    'checkout[shipping_address][phone]': '5038948090',

    'checkout[remember_me]': '',
    'checkout[remember_me]': '0',

    'button': '',

    'checkout[client_details][browser_width]': '1338',
    'checkout[client_details][browser_height]': '829',
    'checkout[client_details][javascript_enabled]': '1',
}

# 第二步：确认联系地址的 webform
form_2 = {
    'utf8': u"\u2713",
    '_method': 'patch',
    'authenticity_token': '',
    'previous_step': 'shipping_method',
    'step': 'payment_method',
    'checkout[shipping_rate][id]': '',
    'button': '',
    'checkout[client_details][browser_width]': '1920',
    'checkout[client_details][browser_height]': '643',
    'checkout[client_details][javascript_enabled]': '1',
}

# 连接mongodb
myclient = pymongo.MongoClient("mongodb://" + conf.mongo['host'] + ':' + conf.mongo['port'])
mydb = myclient["ys"]
mongo = mydb["bypass"]
log = mydb['log']
shoes = mydb['shoes']

# 设置尺码列表
size_arr = {}

# pay 错误信息
pay_error = {
    'CARD WAS DECLINED': '信用卡额度不足',
    'Card number is expired':'卡号已过期',
    'Your card was declined': '您的信用卡遭到拒绝',
    'Street address and postal code do not match.': '街道地址和邮政编码不匹配。',
    'This transaction has been declined': '本次交易已被拒绝',
    'This transaction cannot be processed.': '此交易无法处理。',
    'There was a problem processing the payment. Try a different payment method or try again later.': '处理付款时出现问题。尝试其他付款方式或稍后再试。',
    'No Match': '不匹配',
}

PROXIES_API = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=320000&city=0&yys=0&port=11&pack=51510&ts=0&ys=0&cs=0&lb=4&sb=0&pb=4&mr=1&regions='

# 检测是不是访问过多
def check429(ret, name):
    if ret.status_code == 429:
        msg(name, ret.status_code, '访问次数过多', '访问次数过多')
        return False
    return True

# 判断购物车是否为空
def checkCart(dom):
    soup = BeautifulSoup(dom, "html.parser")
    # 获取到 div class=C__empty
    empty = soup.find('div', class_="C__empty")
    if empty:
        # 获取 C__empty 下子节点
        child = empty.strings
        for v in child:
            if 'YOUR CART IS EMPTY' in v:
                msg('判断购物车是否为空', 200, '购物车为空', v)
                return False

    return True



# 获取代理ip
def getProxies():
    ret = requests.get(PROXIES_API)
    if ret.status_code != 200:
        msg('获取代理IP', ret.status_code, '获取代理ip失败', ret.text)

    ip = {
        'https': 'https://' + ret.text.replace('\n', '')
    }

    msg('获取代理IP', ret.status_code, '成功', ip)

    return ip


# 添加商品
def cartAdd(req):
    params_json = {
        "id": goods_id,
        "quantity": 1,
        "properties": {}
    }

    cart_add = req.post(URL['add'], json=params_json, headers=headers)
    # 检测是否访问次数过多

    if cart_add.status_code != 200:
        msg('添加商品', cart_add.status_code, '接口返回非200', cart_add.json())
        return False

    total_price = cart_add.json()['price']
    total_price = total_price.replace('.', '')

    msg('添加商品', cart_add.status_code, '成功', cart_add.json())

    return total_price


# 获取购物车
def cartGet(req):
    params_form = {
        'updates[]': 1,
        'checkout': 'CHECKOUT'
    }
    cart_get = req.post(URL['cart'], data=params_form, headers=headers)
    # 检测是否访问次数过多
    check429(cart_get, '添加商品')

    if (cart_get.status_code != 200):
        msg('获取购物车', cart_get.status_code, '接口返回非200', cart_get.text)
        return False

    # 判断购物车是否为空
    assert checkCart(cart_get.text)

    msg('获取购物车', cart_get.status_code, '成功', cart_get.text)
    return cart_get.text


# 生成bypass
def bypass(num):
    # 循环生成bp
    for v in range(0, num):

        # 设置 request 对象
        req = requests.session()


        zhima_ip = getProxies()
        req.proxies.update(zhima_ip)

        # 添加商品
        cartAdd(req)

        cart_get = cartGet(req)

        # 获取 auth_token 设置 auth_token
        auth_token = getAuthToken(cart_get)

        form_1['authenticity_token'] = auth_token
        form_2['authenticity_token'] = auth_token
        msg('auth_token-bypass', 200, '成功', auth_token)

        # cookies
        cookies = req.cookies.get_dict()
        msg('获取cookies', 200, '成功', cookies)

        # 拼接bp链接 tracked_start_checkout 在购物车之后才会生成
        if 'tracked_start_checkout' not in cookies:
            msg('拼接 BP 链接', 404, '找不到 cookies["tracked_start_checkout"]', '')
            return False
        bypass = cookies['tracked_start_checkout']
        url = URL['bp'] + str(bypass)
        msg('生成bypass', 200, '成功', url)

        # cookies
        cookies = req.cookies.get_dict()
        msg('获取cookies', 200, '成功', cookies)

        # 储存联系信息
        payment_url = setContact(req, url, cookies)

        # 去除商品
        cart_change = req.post(URL['change'], json={"id": goods_id, "quantity": 0, "properties": {}},headers=headers)
        if (cart_change.status_code != 200):
            msg('去除商品', cart_change.status_code, '接口返回非200', cart_change.json())
        else:
            msg('去除商品', cart_change.status_code, '成功', cart_change.text)

        # 储存至mongodb
        params = {
            'size': 0,
            'pay': 0,
            'cookies': cookies,
            'url': url,
            'auth_token': auth_token,
            'payment_url': payment_url,
            'time': arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'),
            'error': '0',
        }
        ret_add = mongo.insert_one(params)
        if ret_add:
            msg('插入数据', 200, '成功', url)
        else:
            msg('插入数据', 200, '失败', ret_add)

    return req


# 获取订单页的授权auth_token
def getAuthToken(dom):
    soup = BeautifulSoup(dom, "html.parser")
    # 获取到 input name="authenticity_token" 第一个
    auth_token = soup.select('input[name="authenticity_token"]')[0]['value']
    if not auth_token:
        msg('获取auth_token', 404, '找不到 auth_token', auth_token)
        return False

    return auth_token


# 获取订单页的 data-shipping_method
def getShippingMethod(dom):
    soup = BeautifulSoup(dom, "html.parser")
    # class='radio-wrapper'  'data-shipping-method'
    shipping_method = soup.find('div', class_="radio-wrapper").attrs['data-shipping-method']
    if not shipping_method:
        msg('获取shipping_method', 404, '找不到 shipping_method', shipping_method)
        return False

    return shipping_method


# 填写联系信息
def setContact(req, url, cookies):
    cart_contact = req.post(url, data=form_1, cookies=cookies, headers=headers)
    if (cart_contact.status_code != 200):
        msg('储存联系信息', cart_contact.status_code, '接口返回非200', cart_contact.text)
        return False
    else:
        msg('储存联系信息', cart_contact.status_code, '成功', cart_contact.text)

    # 获取 shipping_method
    shipping_method = getShippingMethod(cart_contact.text)
    # 设置 shipping_method
    form_2['checkout[shipping_rate][id]'] = shipping_method

    cart_shipping = req.post(url, data=form_2, cookies=cookies, headers=headers)
    if (cart_contact.status_code != 200):
        msg('确认收货方式', cart_contact.status_code, '接口返回非200', cart_shipping.text)
    else:
        msg('确认收货方式', cart_contact.status_code, '成功', cart_shipping.text)

    return cart_shipping.url


# 获取支付令牌
# def get_payment_token(card_number, cardholder, expiry_month, expiry_year, cvv):
def getPaymentToken(req):
    data = {
        "credit_card": {
            "number": '370288903123969',  # 去掉空格
            "name": '林文强',
            "month": '4',  # 单位数去掉0
            "year": '2025',
            "verification_value": '507'
        }
        # "credit_card": {
        #     "number": '4835910153849545',  # 去掉空格
        #     "name": '林文强',
        #     "month": '4',  # 单位数去掉0
        #     "year": '2028',
        #     "verification_value": '316'
        # }

    }

    ret = req.post(URL['credit'], json=data, headers=headers)
    if ret.status_code != 200:
        msg("获取支付token", ret.status_code, "失败", ret.text)

    msg("获取支付token", ret.status_code, "成功", ret.text)

    payment_token = json.loads(ret.text)["id"]

    return payment_token


# 获取支付网关ID payment_gateway total_price
def getGateway(url, cookies):
    ret = requests.get(url, cookies=cookies, headers=headers)
    if (ret.status_code != 200):
        msg('获取支付网关ID', ret.status_code, '接口返回非200', ret.text)
        return False
    else:
        msg('获取支付网关ID', ret.status_code, '成功', ret.text)

    # 获取 gateway
    soup = BeautifulSoup(ret.text, 'html.parser')
    gateway = soup.find('div', class_='card-fields-container').attrs['data-subfields-for-gateway']
    if gateway is None:
        msg('获取 gateway', 404, '找不到dom', gateway)
        return False
    else:
        msg('获取 gateway', 200, '成功', gateway)

    # 获取 total_price
    total_price = soup.find('span', class_='total-recap__final-price').attrs['data-checkout-payment-due-target']
    if total_price is None:
        msg('获取 total_price', 404, '找不到 dom', total_price)
        return False
    else:
        msg('获取 total_price', 200, '成功', total_price)

    arr = {'gateway': gateway, 'total_price': total_price}

    return arr


''' 以下是抢购流程 '''


# 抢购开始
def start():
    # size_list = search('workwear-shirt-sage')
    msg('开始抢购！', 200, '开始抢购！', arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))
    # 获取尺码ID
    size_arr = getSize()
    if not size_arr:
        msg('获取尺码', 404, '没有可用尺码', '没有可用尺码')
    msg('获取尺码', 200, '成功', size_arr)

    # 获取所有未付款的 bypass
    bp_list = mongo.find_one({'pay': 0, 'error': '0'})


    req = requests.session()

    # 添加代理
    req.proxies.update(getProxies())

    # 代理测试
    ret = req.get('https://icanhazip.com')
    msg("代理测试", ret.status_code, "成功", ret.text)

    # 获取商品总价
    total_price = add(req, bp_list['cookies'], size_arr['id'])

    # 获取购物车 必须要。为了更新cookie
    cart_get = req.post(URL['cart'], json={'updates[]': 1, 'checkout': 'CHECKOUT'},
                        cookies=bp_list['cookies'],
                        headers=headers, proxies=proxies)
    if (cart_get.status_code != 200):
        msg('获取购物车', cart_get.status_code, '接口返回非200', cart_get.text)
        return False
    else:
        msg('获取购物车', cart_get.status_code, '成功', cart_get.text)


    pay(req, bp_list['payment_url'], bp_list['cookies'], bp_list['auth_token'], total_price, size_arr['size'])


# 获取尺码
def getSize():
    # 查询尺码是否还有库存
    for v in buy_size:
        where = {
            'status': 1,
            'size': v
        }
        ret = shoes.find_one(where)
        if ret:
            return {'size': ret['size'], 'id': ret['id']}

    msg('获取尺码', 404, '没有可用尺码', '没有可用尺码')
    return False


# 查找商品
def search(keywords):
    # 判断关键字是否有值
    if not keywords:
        msg('搜索商品-输入关键字', 404, '缺乏参数 keywords', keywords)
        return False

    ''' 无限访问首页直到没有  302重定向 或 失败为止 '''
    num_302 = 0  # 302 重定向重试次数
    num_fail = 0  # 访问失败重试次数
    while True:
        # 访问网站获取Dom
        ret = requests.get(URL['product'] + keywords, allow_redirects=False, proxies=proxies,
                           timeout=timeout)
        # ret = requests.get('http://icanhazip.com', allow_redirects=False, proxies=proxies)
        # 判断页面是否重定向
        if (ret.status_code == 302):
            num_302 += 1
            msg('搜索商品-访问首页', ret.status_code, '页面重定向 302 重连次数：' + str(num_302), '页面重定向 302')
            time.sleep(delay)
            continue

        if (ret.status_code != 200 and ret.status_code != 302):
            num_fail += 1
            msg('搜索商品-访问首页', ret.status_code, '访问失败 重连次数：' + str(num_fail), ret.text)
            time.sleep(delay)
            continue

        msg('搜索商品-访问首页', ret.status_code, '成功 302次数：' + str(num_302) + ' 失败重连：' + str(num_fail), ret.text)
        break

    # 判断Dom是否存在
    soup = BeautifulSoup(ret.text, "html.parser")
    dom_id = 'js-product-json'
    script_content = soup.find(class_=dom_id)
    if script_content is None:
        msg('搜索商品-查找储存json数据的Dom', 404, '找不到 Dom：class=js-product-json', script_content)
        return False

    # 获取 script 里的 json 字符串转换成 字典
    script_content = script_content.get_text()
    product = json.loads(script_content)

    # 获取尺码列表
    size_list = product['variants']
    if not size_list:
        msg('搜索商品-判断尺码列表是否为空', 404, '当前尺码列表 variants 为空', size_list)
        return False

    # 获取可用尺码
    for v in size_list:
        if v['available'] == True:
            size_arr[v['options'][0]] = v['id']

    if not size_arr:
        msg('搜索商品-查找可用尺码', 404, '当前可用 为空', size_list)
        return False

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

    msg('搜索商品-插入搜索到的尺码ID', 200, '成功', size_arr)

    return size_arr


# 获取尺码
def getSize():
    # 查询尺码是否还有库存
    for v in buy_size:
        where = {
            'status': 1,
            'size': v
        }
        ret = shoes.find_one(where)
        if ret:
            return {'size': ret['size'], 'id': ret['id']}

    msg('获取尺码', 404, '没有可用尺码', '没有可用尺码')
    return False


# 添加商品
def add(req, cookies, id):
    cart_add = req.post(URL['add'], json={"id": id, "quantity": 1, "properties": {}},
                        headers=headers, cookies=cookies, proxies=proxies)
    if (cart_add.status_code != 200):
        msg('添加商品', cart_add.status_code, '接口返回非200', cart_add.json())
        return False
    else:
        msg('添加商品', cart_add.status_code, '成功', cart_add.json())

    total_price = cart_add.json()['price']
    total_price = total_price.replace('.', '')

    return total_price


# 付款
def pay(req, url, cookies, auth_token, total_price, size):
    # 获取付款令牌
    payment_token = getPaymentToken(req)

    data = {
        "utf8": u"\u2713",
        "_method": "patch",
        "authenticity_token": auth_token,
        "previous_step": "payment_method",
        "step": "",
        "s": payment_token,
        "checkout[payment_gateway]": gateway,
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
    ret = req.post(url, data=data, cookies=cookies, headers=headers, proxies=proxies)
    if (ret.status_code != 200):
        msg('付款请求：', ret.status_code, '接口返回非200', ret.text)
        return False
    else:
        msg('付款请求：', ret.status_code, '成功', data)

    # 判断付款是否成功
    ret_pay = getPayError(ret.text)
    if ret_pay == True:
        msg('付款：', 200, '成功', '成功')
        # 修改支付状态
        where = {'payment_url': url}
        ret_edit = mongo.update_one(where, {'$set': {
            'size': size,
            'pay': 1,
        }})
        if ret_edit.modified_count == 1:
            msg('付款状态修改：', 200, '成功', "成功")
        else:
            msg('付款状态修改：', 503, '失败', "'失败'")
            return False

        return True
    else:
        msg('付款：', 503, '失败', ret_pay)
        # 修改支付状态
        where = {'payment_url': url}
        ret_edit = mongo.update_one(where, {'$set': {
            'size': size,
            'error': ret_pay,
        }})
        if ret_edit.modified_count == 1:
            msg('付款状态修改：', 200, '成功', '成功')
        else:
            msg('付款状态修改：', 503, '失败', '成功')
            return False

        return False


# 获取支付错误信息
def getPayError(dom):
    soup = BeautifulSoup(dom, 'html.parser')
    error = soup.find('p', class_="notice__text")
    if error is None:
        return True

    error = error.get_text()

    msg("支付信息", 200, "信息", error)
    # 输出中文付款错误
    for k, v in pay_error.items():
        if error in k:
            error = v

    return error


# 信息输出
# def msg(name, code, msg, content,goods,size):
def msg(name, code, msg, content):
    print('[步骤]：', name, end='\n')
    print('[状态]：', code, end='\n')
    print('[说明]：', msg, end='\n')
    if (len(content) > 200):
        print('[内容]：', len(content), end='\n')
    else:
        print('[内容]：', content, end='\n')
    print('---------------------------------------------------', end='\n')

    # 记录log
    log.insert_one({
        # '名称':goods,
        # '尺码':size,
        '步骤': name,
        '状态': code,
        '说明': msg,
        '内容': content,
        '时间': arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'),
    })
    return False


if __name__ == "__main__":
    start_time = arrow.now().timestamp
    loop = asyncio.get_event_loop()

    # 生成bp
    # bypass(1)
    search('flannel-lined-canvas-jacket-black-brown')
    start()

    # 运行时间
    end_time = arrow.now().timestamp
    use_time = end_time - start_time

    msg = '总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))
    print(msg)
