import time

import arrow, random

import requests, pymongo
from bs4 import BeautifulSoup
import json, threading

''' 初始设置 '''

# 开始加入购物车的id
GOODS_ID = '707316252691'

# 设置购买尺码
buy_size = ['L', 'M']

# 设置gateway
gateway = '117647559'

# 访问延迟时间
delay = 1

# 设置超时时间
TIMEOUT = 20

# 设置一个ip 创建 bypass 数量
IP_BYPASS_NUM = 40

''' 初始设置 '''

# 域名
HOST = 'https://yeezysupply.com'
# 接口
URL = {
    'add': HOST + '/cart/add.json',
    'change': HOST + '/cart/change.json',
    'cart': HOST + '/cart',
    'bp': HOST + '/17655971/checkouts/',
    'product': HOST + '/products/',
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
HEADERS = {
    'User-Agent': user_agent
}
# 设置芝麻代理 URL
PROXIES_API = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=320000&city=0&yys=0&port=11&time=1&ts=0&ys=0&cs=0&lb=6&sb=0&pb=4&mr=1&regions='

# 第一步：联系地址 订单的webForm
form_1 = {
    'utf8': u"\u2713",
    '_method': 'patch',
    'authenticity_token': '',  # 通过购物车Dom获取
    'previous_step': 'contact_information',
    'step': 'shipping_method',

    # 'checkout[email]': 'snkrs_japan@163.com',
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
myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017")
mydb = myclient["ys"]
mongo = mydb["bypass"]
log = mydb['log']
pay_log = mydb['pay_log']
shoes = mydb['shoes']

# 设置尺码列表
size_arr = {}



# 获取代理ip
def getProxies():
    ret = requests.get(PROXIES_API)
    if ret.status_code != 200:
        reqMsg('获取代理IP', ret.status_code, '获取代理ip失败', ret.text)

    ip = {
        'https': 'https://' + ret.text
    }

    reqMsg('获取代理IP', ret.status_code, '成功', ip)

    return ip


# 测试代理是否成功
def testProxies(req):
    ret = req.get('https://icanhazip.com')

    reqMsg("当前ip:", ret.status_code, '成功', ret.text)


# 检测是不是访问过多
def check429(ret, name):
    if ret.status_code == 429:
        reqMsg(name, ret.status_code, '访问次数过多', '访问次数过多')
        return False
    return True


# 添加商品
def cartAdd(req):
    params_json = {
        "id": GOODS_ID,
        "quantity": 1,
        "properties": {}
    }

    cart_add = req.post(URL['add'], json=params_json, headers=HEADERS)
    # 检测是否访问次数过多
    check429(cart_add, '添加商品')

    if cart_add.status_code != 200:
        reqMsg('添加商品', cart_add.status_code, '接口返回非200', cart_add.json())
        return False

    total_price = cart_add.json()['price']
    total_price = total_price.replace('.', '')

    reqMsg('添加商品', cart_add.status_code, '成功', cart_add.json())

    return total_price


# 获取购物车
def cartGet(req):
    params_form = {
        'updates[]': 1,
        'checkout': 'CHECKOUT'
    }
    cart_get = req.post(URL['cart'], data=params_form, headers=HEADERS)
    # 检测是否访问次数过多
    check429(cart_get, '添加商品')

    if (cart_get.status_code != 200):
        reqMsg('获取购物车', cart_get.status_code, '接口返回非200', cart_get.text)
        return False

    # 判断购物车是否为空
    assert checkCart(cart_get.text)

    reqMsg('获取购物车', cart_get.status_code, '成功', cart_get.text)
    return cart_get.text


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
                reqMsg('判断购物车是否为空', 200, '购物车为空', v)
                return False

    return True


# 拼接bypass URL
def getUrl(cookies):
    # 拼接bp链接 tracked_start_checkout 在购物车之后才会生成
    if 'tracked_start_checkout' not in cookies:
        reqMsg('拼接 BP 链接', 404, '找不到 cookies["tracked_start_checkout"]', '')
        return False

    bypass = cookies['tracked_start_checkout']
    url = URL['bp'] + str(bypass)

    reqMsg('生成bypass', 200, '成功', url)

    return url


# 去除商品
def cartDel(req):
    # 去除商品
    params_json = {
        "id": GOODS_ID,
        "quantity": 0,
        "properties": {}
    }
    cart_change = req.post(URL['change'], json=params_json, headers=HEADERS)
    if (cart_change.status_code != 200):
        reqMsg('去除商品', cart_change.status_code, '接口返回非200', cart_change.json())

    reqMsg('去除商品', cart_change.status_code, '成功', cart_change.text)
    return True


# 生成bypass
def bypass(zhima_ip):
    # 设置 request 对象
    req = requests.session()
    # 设置代理
    if zhima_ip:
        req.proxies.update(zhima_ip)

    # 添加商品
    assert cartAdd(req)

    # 获取购物车
    cart_text = cartGet(req)
    if not cart_text:
        return

    # 获取 auth_token 设置 auth_token
    auth_token = getAuthToken(cart_text)
    if not auth_token:
        return
    form_1['authenticity_token'] = auth_token
    form_2['authenticity_token'] = auth_token
    reqMsg('auth_token-bypass', 200, '成功', str(auth_token))

    # cookies
    cookies = req.cookies.get_dict()
    reqMsg('获取cookies', 200, '成功', cookies)

    # 获取bypass url
    url = getUrl(cookies)
    if not url:
        return

    # 储存联系信息
    payment_url = setContact(req, url, cookies)

    # 获取付款令牌
    payment_token = getPaymentToken()

    # 去除商品
    cart_change = req.post(URL['change'], json={"id": GOODS_ID, "quantity": 0, "properties": {}},
                           cookies=req.cookies.get_dict(),
                           headers=headers)
    if (cart_change.status_code != 200):
        reqMsg('去除商品', cart_change.status_code, '接口返回非200', cart_change.json())
    else:
        reqMsg('去除商品', cart_change.status_code, '成功', cart_change.text)

    # 更新cookies 获取最新cookies
    cookies = req.cookies.get_dict()

    # 储存至mongodb
    params = {
        'size': 0,
        'pay': 0,
        'get': 0,
        'cookies': cookies,
        'url': url,
        'auth_token': auth_token,
        'payment_token': payment_token,
        'payment_url': payment_url,
        'time': arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'),
        'error': 0,
    }
    ret_add = mongo.insert_one(params)
    if ret_add:
        reqMsg('插入数据', 200, '成功', url)
    else:
        reqMsg('插入数据', 200, '失败', ret_add)

    return req


# 获取订单页的授权auth_token
def getAuthToken(dom):
    soup = BeautifulSoup(dom, "html.parser")
    # 获取到 input name="authenticity_token" 第一个
    auth_token = soup.select('input[name="authenticity_token"]')
    if not auth_token:
        reqMsg('获取auth_token', 404, '找不到 auth_token', auth_token)
        return False

    auth_token = auth_token[0]['value']

    return auth_token


# 获取订单页的 data-shipping_method
def getShippingMethod(dom):
    soup = BeautifulSoup(dom, "html.parser")
    # class='radio-wrapper'  'data-shipping-method'
    shipping_method = soup.find('div', class_="radio-wrapper").attrs['data-shipping-method']
    if not shipping_method:
        reqMsg('获取shipping_method', 404, '找不到 shipping_method', shipping_method)
        return False

    return shipping_method


# 填写联系信息
def setContact(req, url, cookies):
    cart_contact = req.post(url, data=form_1, cookies=cookies, headers=HEADERS)
    if (cart_contact.status_code != 200):
        reqMsg('储存联系信息', cart_contact.status_code, '接口返回非200', cart_contact.text)
        return False
    else:
        reqMsg('储存联系信息', cart_contact.status_code, '成功', cart_contact.text)

    # 获取 shipping_method
    shipping_method = getShippingMethod(cart_contact.text)
    # 设置 shipping_method
    form_2['checkout[shipping_rate][id]'] = shipping_method

    cart_shipping = req.post(url, data=form_2, cookies=cookies, headers=HEADERS)
    if (cart_contact.status_code != 200):
        reqMsg('确认收货方式', cart_contact.status_code, '接口返回非200', cart_shipping.text)
    else:
        reqMsg('确认收货方式', cart_contact.status_code, '成功', cart_shipping.text)

    return cart_shipping.url


# 获取支付网关ID payment_gateway total_price
def getGateway(url, cookies):
    ret = requests.get(url, cookies=cookies, headers=HEADERS)
    if (ret.status_code != 200):
        reqMsg('获取支付网关ID', ret.status_code, '接口返回非200', ret.text)
        return False
    else:
        reqMsg('获取支付网关ID', ret.status_code, '成功', ret.text)

    # 获取 gateway
    soup = BeautifulSoup(ret.text, 'html.parser')
    gateway = soup.find('div', class_='card-fields-container').attrs['data-subfields-for-gateway']
    if gateway is None:
        reqMsg('获取 gateway', 404, '找不到dom', gateway)
        return False
    else:
        reqMsg('获取 gateway', 200, '成功', gateway)

    # 获取 total_price
    total_price = soup.find('span', class_='total-recap__final-price').attrs['data-checkout-payment-due-target']
    if total_price is None:
        reqMsg('获取 total_price', 404, '找不到 dom', total_price)
        return False
    else:
        reqMsg('获取 total_price', 200, '成功', total_price)

    arr = {'gateway': gateway, 'total_price': total_price}

    return arr


# 获取支付令牌
def getPaymentToken():
    params_json = {
        "credit_card": {
            "number": '370288903123969',  # 去掉空格
            "name": '林文强',
            "month": '4',  # 单位数去掉0
            "year": '2025',
            "verification_value": '507'
        }
    }

    ret = requests.post(URL['credit'], json=params_json, headers=HEADERS)
    payment_token = json.loads(ret.text)["id"]

    return payment_token


# 信息输出
def reqMsg(name, code, msg, content):
    print('[步骤]：', name, end='\n')
    print('[状态]：', code, end='\n')
    print('[说明]：', msg, end='\n')
    if (len(str(content)) > 200):
        print('[内容]：', len(content), end='\n')
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
    log.insert_one(log_info)


# 开启线程
def threadBypass(zhima_ip):
    # 生成bp
    task_number = IP_BYPASS_NUM

    i = 1
    tasks = []
    while i <= task_number:
        reqMsg('开启 第 ' + str(i) + " 个线程", 200, '成功', '成功')
        t = threading.Thread(target=bypass, args=(zhima_ip,))
        tasks.append(t)
        t.start()
        i += 1


if __name__ == "__main__":

    start_time = arrow.now().timestamp

    for v in range(1, 2):
        zhima_ip = getProxies()
        threadBypass(zhima_ip)
        time.sleep(2)

    # 运行时间
    end_time = arrow.now().timestamp
    use_time = end_time - start_time

    msg = '总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))
    print(msg)
