import common.conf as conf
import common.phone as phoneSdk
import common.randomName as nameSdk

import nikeDriver
import requests, random, arrow, pymongo

HOST = "https://unite.nike.com/"
HOST_IDN = "https://idn.nike.com/"

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

HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
}

PROXIES = False
FIDDLER = False
DEBUG = False

# 链接mongodb
myclient = pymongo.MongoClient("mongodb://" + conf.mongo['host'] + ':' + conf.mongo['port'])
mydb = myclient["nike"]
db_account = mydb["account"]


# 测试代理是否成功
def testProxies(req):
    ret = req.get('https://icanhazip.com')

    print("当前代理ip:", ret.status_code, '成功', ret.text)
    return True


# 获取代理ip
def getProxies(https=True):
    if https:
        url = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=320000&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=6&sb=0&pb=4&mr=1&regions='
    else:
        url = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=320000&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=6&sb=0&pb=4&mr=2&regions='

    ret = requests.get(url)
    if ret.status_code != 200:
        print('获取代理IP', ret.status_code, '获取代理ip失败', ret.text)

    if https:
        ip = {'https': ret.text}
    else:
        ip = {'http': ret.text}

    print('获取代理IP', ret.status_code, '成功', ip)

    return ip


def generateAlphanumeric(length):
    return ''.join(random.choices('0123456789abcdefABCDEF', k=length))


# 获取访客ID
def getVisitId():
    # 为匹配正则表达式的nike请求生成随机ID：
    # ^ [0-9a-fA-F] {8}  -  [0-9a-fA-F] {4}  -  [0-9a-fA-F] {4}  -  [0-9a-fA-F] {4} - [0-9A-FA-F] {12} $
    # 即c287c8b3-bd5f-4341-959c-d9121997662c
    id = generateAlphanumeric(8) + '-' \
         + generateAlphanumeric(4) + '-' \
         + generateAlphanumeric(4) + '-' \
         + generateAlphanumeric(4) + '-' \
         + generateAlphanumeric(12)

    PARAMS['visitor'] = id

    msg("生成Visit_id", 200, id)
    return id


# 获取 abck 的cookie 用于注册
def getSession(req):
    url = 'https://s3.nikecdn.com/_bm/_data'
    referer = 'https://s3.nikecdn.com/unite/mobile.html'
    origin = 'https://s3.nikecdn.com'

    headers = {
        "Connection": "keep-alive",
        "X-NewRelic-ID": "VQYGVF5SCBAJVlFaAQIH",
        "Origin": origin,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36",
        "Content-Type": "text/plain;charset=UTF-8",
        "Accept": "*/*",
        "Referer": referer,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,ms;q=0.8"
    }


# 发送短信
def sendPhone(req):
    url = HOST + 'phoneVerification'

    # 生成访问ID
    getVisitId()

    phone = phoneSdk.getPhone(723)

    PARAMS['phoneNumber'] = "86" + str(phone)
    PARAMS['country'] = "CN"

    ret = req.post(url, params=PARAMS, data={}, headers=HEADER)
    if ret.status_code != 204:
        msg('NIKE发送短信', ret.status_code, "失败！")
        return False

    msg("NIKE发送短信", ret.status_code, "成功！")

    token = getRegisterToken(req, phone)
    if not token:
        return False

    info = {
        'phone': phone,
        'token': token,
    }

    return info


# 校验短信验证码 换取token
def getRegisterToken(req, phone):
    url = HOST + 'registrationToken'

    # 获取短信验证码
    code = phoneSdk.getSms(phone, 723)
    if not code:
        return False

    json = {
        'verificationCode': str(code)
    }

    ret = req.post(url, params=PARAMS, json=json, headers=HEADER)
    if ret.status_code != 200:
        msg("验证码校验", ret.status_code, "接口异常！")
        return False

    token = ret.json()['registrationToken']

    return token


# 注册账号
def register():
    req = requests.session()

    if FIDDLER:
        proxies = {'http': '127.0.0.1:8888'}
        req.proxies.update(proxies)
        req.verify = False
    else:
        if PROXIES:
            # # 设置 芝麻代理 ip
            req.proxies.update(getProxies())

            if DEBUG:
                testProxies(req)

    # 发送短信
    info = sendPhone(req)
    if not info:
        return False

    url = HOST + 'access/users/v1'

    # 获取姓名
    name = nameSdk.getName()

    json = {
        "country": "CN",
        "emailOnly": False,
        "firstName": name['mz'],
        "lastName": name['xm'],
        "gender": "M",
        "locale": "zh_CN",
        "password": "Mn476489634",
        "receiveEmail": False,
        "receiveSms": True,
        "registrationSiteId": "nikedotcom",
        "registrationToken": info['token'],
        "welcomeEmailTemplate": "TSD_PROF_COMM_WELCOME_V1.0",
        "mobileNumber": "+86" + str(info['phone']),
        "ssn": "",
        "account": {
            "passwordSettings": {
                "password": "Mn476489634",
                "passwordConfirm": "Mn476489634"
            }
        },
        "minimumAge": 13,
        "minimumAgeReason": "TERMS"
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36',
        'Referer': 'https://www.nike.com/cn/',
        'Origin': 'https://www.nike.com',
        'Content-Type': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    req.cookies["CONSUMERCHOICE"] = "cn/zh_cn"
    req.cookies["NIKE_COMMERCE_COUNTRY"] = "CN"
    req.cookies["NIKE_COMMERCE_LANG_LOCALE"] = "zh_CN"
    req.cookies["nike_locale"] = "cn/zh_cn"
    req.headers.update(headers)
    print(req.headers)
    print(req.cookies.get_dict())

    ret = req.post(url, params=PARAMS, json=json, timeout=20)

    if ret.status_code != 201:
        msg('账号设置接口异常', ret.status_code, ret.text)
        return False

    account = {
        'phone': info['phone'],
        'token': info['token'],
        'name': name['mz'] + name['xm'],
    }

    msg('账号设置成功', ret.status_code, account)

    # 拉黑手机号
    phoneSdk.ignore(info['phone'], 723)

    # 获取access_token
    access_token = login(req, info['phone'])
    if not access_token:
        return False

    # 设置邮箱
    email = setEmail(req, access_token)
    if not email:
        return False

    # 插入数据库
    data = {
        'phone': info['phone'],
        'name': account['name'],
        'address': "",
        'refresh_token': "",
        'access_token': access_token,
        'email': email,
        'time': arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss'),
    }
    ret = db_account.insert_one(data)
    if ret.acknowledged:
        print("保存账号成功", 200, data)
    else:
        print("保存账号失败", 500, data)

    # 获取refresh_token 设置地址
    refresh_token = nikeDriver.login(info['phone'])

    # 获取长期 access_token
    getAccessToken(info['phone'], refresh_token)

    return account


# 设置邮箱
def setEmail(req, access_token):
    url = HOST + 'updateUser'

    random_email = random.randint(1000000000, 99999999999) + random.randint(1, 10)
    email = str(random_email) + "@qq.com"

    json = {
        "dob": {
            "date": 792806400000
        },
        "emails": {
            "primary": {
                "email": email
            }
        }
    }

    headers = {"authorization": "Bearer " + access_token}

    ret = req.post(url, params=PARAMS, json=json, proxies=PROXIES, headers=headers)
    if ret.status_code != 202:
        msg('邮箱设置设置接口异常', ret.status_code, ret.text)
        return False

    msg('邮箱设置设置成功', ret.status_code, email)

    return email


# 获取用户信息
def getUser(req, access_token):
    url = HOST + 'getUserService'
    headers = {"authorization": "Bearer " + access_token}

    PARAMS['viewId'] = 'unite'
    PARAMS['atgSync'] = 'true'

    ret = req.get(url, params=PARAMS, headers=headers, proxies=PROXIES)
    if ret.status_code != 200:
        msg('获取用户信息接口异常', ret.status_code, ret.text)
        return False
    try:
        guid = ret.json()['address']['shipping']['guid']
    except:
        guid = ret.json()['upmId']

    msg('获取用户信息成功', ret.status_code, 'guid：' + guid)

    return guid


# 获取access_token
def getAccessToken(phone, refresh_token):
    Timeout = 20

    url = 'https://api.nike.com/idn/shim/oauth/2.0/token'
    json = {
        'client_id': 'HlHa2Cje3ctlaOqnxvgZXNaAs7T9nAuH',
        'grant_type': 'refresh_token',
        'ux_id': 'com.nike.commerce.snkrs.ios',
        'refresh_token': refresh_token,
    }
    num = 1
    while num <= 3:
        try:
            ret = requests.post(url, json=json, timeout=Timeout, proxies=PROXIES)
            break
        except:
            msg('获取AccessToken', ret.status_code, '代理连接失败')
            num += 1
            continue
    try:
        access_token = ret.json()['access_token']
    except:
        access_token = ret.json()
        msg('更新AccessToken', 500, ret.json())

    # 更新数据库
    where = {
        'phone': phone
    }
    ret = db_account.update_one(where, {'$set': {
        'access_token': access_token,
    }}, upsert=True)

    if ret.acknowledged:
        print("更新AccessToken：", "成功", "手机号：", phone)
    else:
        print("更新AccessToken：", "失败", "手机号：", phone)

    return access_token


# 登录
def login(req, phone):
    if 'visitor' not in PARAMS:
        getVisitId()

    url = HOST + 'login'

    username = "+86" + str(phone)

    json = {
        "username": username,
        "password": "Mn476489634",
        "client_id": 'HlHa2Cje3ctlaOqnxvgZXNaAs7T9nAuH',
        "ux_id": "com.nike.commerce.nikedotcom.web",
        "grant_type": "password"
    }

    headers = {
        'Origin': 'https://www.nike.com',
        'Referer': 'https://www.nike.com/cn/',
    }

    ret = req.post(url, params=PARAMS, json=json, proxies=PROXIES, headers=headers)
    if ret.status_code != 200:
        msg("登录错误", ret.status_code, ret.text)
        msg("登录错误", ret.status_code, json)
        return False

    access_token = ret.json()['access_token']
    msg("登录成功", ret.status_code, access_token)

    return access_token


def msg(name, status, content, line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    phone = register()
