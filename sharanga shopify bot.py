'''
sharanga shopify bot v1.1
shopify bot（WIP）
由@snivynGOD开发

TO-DO
 - 检查付款是否成功或失败
 - 可能获得身份验证令牌？但似乎并不需要
 - 可能得到验证码？不确定是否需要（如果是这样，创建验证码解决模块）
 - 为像KITH和DSMNY这样使用不同链接的网站添加模块
products (https://kith.com/collections/all/products.atom)
 - 使用GUI和多线程在C＃中重写，一次支持多个任务（即将推出）
 - 符合PEP8标准

效率待办事项
不是非常有效，但它会有所帮助

- 用户点击按钮预加载付款令牌（即用户可以点击按钮
在丢弃之前获取支付令牌，以便在任务期间不浪费资源
试图获取令牌）或异步获取付款令牌
- 通过指定一个站点列表来预加载网关，但也保留选项
用户输入shopify网站以确保尽可能多的站点得到支持
'''

from bs4 import BeautifulSoup as soup
import requests
import time
import json
import urllib3
import codecs
import random


''' ------------------------------ SETTINGS ------------------------------ '''
# 全局设置
base_url = "https://www.deadstock.ca"  # 不要在末尾添加/

# 搜索设置
keywords = ["adidas", "cs2"]  # 用逗号分隔关键字
size = "11"

# 如果尺码售罄，将选择随机尺寸作为备用计划
random_size = True

# 为避免Shopify软禁，建议延迟7.5秒
# 比发布时间（发布前几分钟）更早地启动任务
# 否则，1秒或更短的延迟将是理想的
search_delay = 1

# 结帐设置
email = "email@domain.com"
fname = "Bill"
lname = "Nye"
addy1 = "123 Jolly St"
addy2 = ""  # 可以留空
city = "Toronto"
province = "Ontario"
country = "Canada"
postal_code = "M1G1E4"
phone = "4169671111"
card_number = "4510000000000000"  # 没有空格
cardholder = "FirstName LastName"
exp_m = "12"  # 2位数
exp_y = "2017"  # 4位数
cvv = "666"  # 3位数

''' ------------------------------- MODULES ------------------------------- '''


def get_products(session):
    '''
     获取Shopify网站上的所有产品。
    '''
    # 下载产品
    link = base_url + "/products.json"
    r = session.get(link, verify=False)

    # 加载产品数据
    products_json = json.loads(r.text)
    products = products_json["products"]

    # 退回产品
    return products


def keyword_search(session, products, keywords):
    '''
    从Shopify网站搜索给定产品以查找产品
    包含所有已定义的关键字。
    '''
    # 浏览每个产品
    for product in products:
        # 设置计数器以检查是否找到所有关键字
        keys = 0
        # 浏览每个关键字
        for keyword in keywords:
            # 如果标题中存在关键字
            if(keyword.upper() in product["title"].upper()):
                # 递增计数器
                keys += 1
            # 如果找到所有关键字
            if(keys == len(keywords)):
                # 返回产品
                return product


def find_size(session, product, size):
    '''
    从Shopify网站查找产品的指定大小。
    '''
    # 浏览产品的每个变体 variant
    for variant in product["variants"]:
        # 检查是否找到了尺寸
        # 如果网站列出的尺寸为11美元，请使用'in'代替'=='
        if(size in variant["title"]):
            variant = str(variant["id"])

            # 返回大小的变体
            return variant

    # 如果未找到大小但启用了随机大小
    if(random_size):
        # 初始化变体列表
        variants = []

        # 将所有变体添加到列表中
        for variant in product["variants"]:
            variants.append(variant["id"])

        # 随机选择一个变体
        variant = str(random.choice(variants))

        # 返回结果
        return variant


def generate_cart_link(session, variant):
    '''
    给定变体ID，为Shopify网站生成添加到购物车链接。
    '''
    # 创建链接以将产品添加到购物车
    link = base_url + "/cart/" + variant + ":1"

    # 返回链接
    return link


def get_payment_token(card_number, cardholder, expiry_month, expiry_year, cvv):
    '''
    鉴于信用卡详细信息，Shopify结帐的付款令牌是回。
    '''
    # POST信息来获得支付令牌
    link = "https://elb.deposit.shopifycs.com/sessions"

    payload = {
        "credit_card": {
            "number": card_number,
            "name": cardholder,
            "month": expiry_month,
            "year": expiry_year,
            "verification_value": cvv
        }
    }

    r = requests.post(link, json=payload, verify=False)

    # 提取付款令牌
    payment_token = json.loads(r.text)["id"]

    # 返回付款令牌
    return payment_token


def get_shipping(postal_code, country, province, cookie_jar):
    '''
    给定地址详细信息和Shopify结账会话的cookie，将返回送货选项
    '''
    # 从Shopify网站获取运费信息
    link = base_url + "//cart/shipping_rates.json?shipping_address[zip]=" + postal_code + "&shipping_address[country]=" + country + "&shipping_address[province]=" + province
    r = session.get(link, cookies=cookie_jar, verify=False)

    # 加载送货选项
    shipping_options = json.loads(r.text)

    # 选择第一个送货选项
    ship_opt = shipping_options["shipping_rates"][0]["name"].replace(' ', "%20")
    ship_prc = shipping_options["shipping_rates"][0]["price"]

    # 生成运送代币以提交结帐
    shipping_option = "shopify-" + ship_opt + "-" + ship_prc

    # 退回送货选项
    return shipping_option


def add_to_cart(session, variant):
    '''
    给定会话和变体ID，产品将添加到购物然后返回。
    '''
    # 将产品添加到购物车
    link = base_url + "/cart/add.js?quantity=1&id=" + variant
    response = session.get(link, verify=False)

    # 返回
    return response


def submit_customer_info(session, cookie_jar):
    '''
    给出Shopify结账的会话和cookie，客户的信息
    提交。
    '''
    # Submit the customer info
    payload = {
        "utf8": u"\u2713",
        "_method": "patch",
        "authenticity_token": "",
        "previous_step": "contact_information",
        "step": "shipping_method",
        "checkout[email]": email,
        "checkout[buyer_accepts_marketing]": "0",
        "checkout[shipping_address][first_name]": fname,
        "checkout[shipping_address][last_name]": lname,
        "checkout[shipping_address][company]": "",
        "checkout[shipping_address][address1]": addy1,
        "checkout[shipping_address][address2]": addy2,
        "checkout[shipping_address][city]": city,
        "checkout[shipping_address][country]": country,
        "checkout[shipping_address][province]": province,
        "checkout[shipping_address][zip]": postal_code,
        "checkout[shipping_address][phone]": phone,
        "checkout[remember_me]": "0",
        "checkout[client_details][browser_width]": "1710",
        "checkout[client_details][browser_height]": "1289",
        "checkout[client_details][javascript_enabled]": "1",
        "button": ""
    }

    link = base_url + "//checkout.json"
    response = session.get(link, cookies=cookie_jar, verify=False)

    # 获取结帐网址
    link = response.url
    checkout_link = link

    # 将数据发布到结帐URL
    response = session.post(link, cookies=cookie_jar, data=payload, verify=False)

    # 返回响应和结账链接
    return (response, checkout_link)

''' ------------------------------- CODE ------------------------------- '''

# 初始化
session = requests.session()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
product = None

# 循环，直到找到包含所有关键字的产品
while(product == None):
    # 抓住网站上的所有产品
    products = get_products(session)
    # 抓住关键字定义的产品
    product = keyword_search(session, products, keywords)
    if(product == None):
        time.sleep(search_delay)

# 获取大小的ID
variant = find_size(session, product, size)

# 获取购物车链接
cart_link = generate_cart_link(session, variant)

# 将产品添加到购物车
r = add_to_cart(session, variant)

# 存储cookie
cj = r.cookies

# 获取付款令牌
p = get_payment_token(card_number, cardholder, exp_m, exp_y, cvv)

# 提交客户信息并获取结帐网址
(r, checkout_link) = submit_customer_info(session, cj)

# 获取送货信息
ship = get_shipping(postal_code, country, province, cj)

# 获取支付网关ID
link = checkout_link + "?step=payment_method"
r = session.get(link, cookies=cj, verify=False)

bs = soup(r.text, "html.parser")
div = bs.find("div", {"class": "radio__input"})
print(div)

gateway = ""
values = str(div.input).split('"')
for value in values:
    if value.isnumeric():
        gateway = value
        break

# 提交付款
link = checkout_link
payload = {
    "utf8": u"\u2713",
    "_method": "patch",
    "authenticity_token": "",
    "previous_step": "payment_method",
    "step": "",
    "s": p,
    "checkout[payment_gateway]": gateway,
    "checkout[credit_card][vault]": "false",
    "checkout[different_billing_address]": "true",
    "checkout[billing_address][first_name]": fname,
    "checkout[billing_address][last_name]": lname,
    "checkout[billing_address][address1]": addy1,
    "checkout[billing_address][address2]": addy2,
    "checkout[billing_address][city]": city,
    "checkout[billing_address][country]": country,
    "checkout[billing_address][province]": province,
    "checkout[billing_address][zip]": postal_code,
    "checkout[billing_address][phone]": phone,
    "checkout[shipping_rate][id]": ship,
    "complete": "1",
    "checkout[client_details][browser_width]": str(random.randint(1000, 2000)),
    "checkout[client_details][browser_height]": str(random.randint(1000, 2000)),
    "checkout[client_details][javascript_enabled]": "1",
    "g-recaptcha-repsonse": "",
    "button": ""
    }

r = session.post(link, cookies=cj, data=payload, verify=False)
