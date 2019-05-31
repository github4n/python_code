import common.conf as conf
import common.phone as phoneSdk
import common.randomName as nameSdk

import nikeDriver
import requests, random, arrow, pymongo

HOST = "https://unite.nike.com/"
HOST_IDN = "https://idn.nike.com/"

APP = True

if APP:
    PARAMS = {
        'appVersion': "595",
        'experienceVersion': "493",
        'uxId': "com.nike.commerce.snkrs.droid",
        'locale': "zh_CN",
        'backendEnvironment': "identity",
        'browser': "Google Inc.",
        'os': "undefined",
        'mobile': "true",
        'native': "true",
        'visit': "1",
        'language': 'zh-Hans',
    }
else:
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

    before(req)

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


# 前置条件
def before(req):

    ret = req.get("https://www.nike.com/cn/")
    print('web:',ret.cookies.get_dict())
    headers = {
        'Referer': 'https://www.nike.com/cn/',
        'Origin': 'https://www.nike.com',

        'X-Requested-With': 'com.nike.snkrs',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Connection': 'keep-alive',
        'X-NewRelic-ID': 'UwcDVlVUGwIHUVZXAQMHUA==',
    }

    json = {
        "sensor_data": "7a74G7m23Vrp0o5c9083451.41-1,2,-94,-100,Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36,uaend,12147,20030107,zh-CN,Gecko,3,0,0,0,383654,9224241,1920,1040,1920,1080,1920,969,1920,,cpen:0,i1:0,dm:0,cwen:0,non:1,opc:0,fc:0,sc:0,wrc:1,isc:0,vib:1,bat:1,x11:0,x12:1,8295,0.932556441466,779634612120,loc:-1,2,-94,-101,do_en,dm_en,t_en-1,2,-94,-105,0,0,0,0,2043,630,0;-1,2,-94,-102,0,0,0,0,2043,630,0;0,0,0,0,2313,821,0;0,0,0,0,2417,937,0;1,2,0,0,2361,883,0;-1,2,-94,-108,0,2,7116,9,0,0,-1;1,1,17435,17,0,4,2460;2,2,17595,17,0,0,2460;3,1,17727,17,0,4,2460;4,1,17875,86,0,4,2460;5,2,17948,17,0,0,2460;6,2,17948,-2,0,0,2460;7,1,18691,18,0,1,-1;8,2,19596,9,0,0,2109;9,1,33950,17,0,4,2109;10,1,34021,86,0,4,2109;11,2,34086,17,0,0,2109;12,2,34101,-2,0,0,2109;-1,2,-94,-110,0,1,7022,1522,67;1,1,7032,1534,65;2,1,7048,1550,64;3,1,7065,1567,60;4,1,7082,1581,59;5,1,7098,1600,59;6,1,7116,1625,59;7,1,7132,1639,61;8,1,7149,1652,62;9,1,7165,1663,64;10,1,7182,1670,65;11,1,7198,1673,67;12,1,7215,1675,68;13,1,7235,1676,68;14,1,7251,1676,70;15,1,7275,1676,71;16,1,7283,1676,72;17,1,7298,1676,73;18,1,7315,1676,75;19,1,7332,1675,77;20,1,7380,1674,77;21,1,7395,1674,76;22,1,7403,1673,74;23,1,7415,1672,73;24,1,7431,1671,65;25,1,7448,1670,61;26,1,7464,1669,56;27,1,7481,1667,51;28,1,7499,1666,47;29,1,7515,1666,44;30,1,7531,1665,41;31,1,7548,1665,39;32,1,7565,1665,38;33,1,7582,1665,34;34,1,7599,1665,31;35,1,7616,1665,28;36,1,7633,1665,25;37,1,7649,1666,25;38,1,7666,1666,24;39,3,7732,1666,24,-1;40,4,7804,1666,24,-1;41,2,7805,1666,24,-1;42,1,7907,1660,41;43,1,7917,1653,50;44,1,7933,1645,61;45,1,7950,1632,75;46,1,7967,1614,92;47,1,7983,1595,110;48,1,8000,1565,128;49,1,8018,1529,152;50,1,8034,1481,179;51,1,8052,1428,204;52,1,8068,1337,235;53,1,8084,1268,252;54,1,8106,1201,263;55,1,8124,1135,280;56,1,8137,1078,290;57,1,8174,1039,301;58,1,8184,971,310;59,1,8202,941,315;60,1,8219,919,319;61,1,8234,903,326;62,1,8250,892,329;63,1,8269,882,331;64,1,8285,877,333;65,1,8300,873,337;66,1,8317,869,342;67,1,8333,866,346;68,1,8369,864,352;69,1,8382,864,355;70,1,8399,864,358;71,1,8416,866,362;72,1,8432,869,366;73,1,8449,874,372;74,1,8465,877,381;75,1,8482,882,388;76,1,8498,889,398;77,1,8515,897,408;78,1,8532,906,414;79,1,8549,917,427;80,1,8565,927,433;81,1,8582,934,440;82,1,8598,942,443;83,1,8616,949,447;84,1,8632,957,450;85,1,8649,965,455;86,1,8665,972,459;87,1,8683,979,465;88,1,8699,990,480;89,1,8716,996,492;90,1,8732,1002,507;91,1,8749,1002,523;92,1,8765,1002,541;93,1,8782,1002,553;94,1,8800,1002,567;95,1,8816,1000,581;96,1,8832,999,588;97,1,8849,999,593;98,1,8865,999,597;99,1,8883,995,607;100,1,8899,993,621;101,1,8916,989,639;102,1,8932,989,646;113,3,9291,984,676,2331;114,4,9380,984,676,2331;115,2,9380,984,676,2331;123,3,9820,985,684,2428;124,4,9891,985,684,2428;125,2,9893,985,684,2428;150,3,10507,992,471,2460;152,4,10581,992,471,2460;153,2,10581,992,471,2460;250,3,18166,1078,462,2477;251,4,18219,1078,462,2477;252,2,18219,1078,462,2477;366,3,33750,938,506,2109;367,4,33829,938,506,2109;368,2,33829,938,506,2109;401,3,34549,957,662,2473;402,4,34614,957,662,2473;403,2,34614,957,662,2473;454,3,36413,870,402,821;-1,2,-94,-117,-1,2,-94,-111,0,118,-1,-1,-1;-1,2,-94,-109,0,117,-1,-1,-1,-1,-1,-1,-1,-1,-1;-1,2,-94,-114,-1,2,-94,-103,3,7018;2,11464;3,16944;2,18782;3,19584;2,20598;3,30486;2,30973;3,32960;-1,2,-94,-112,https://www.nike.com/cn/-1,2,-94,-115,313818,1407891,0,118,117,0,1721942,36413,0,1559269224240,5,16680,13,455,2780,15,0,36414,1497264,0,F1462266802155339CD74F77141E0960~-1~YAAQM2UzuIE/ks1qAQAAvKawCwHc92McE7PycrDaW95RDNS6/CGfAcdG1TTJFlTjXvMyR7//o2nH35I6FIFzYdEeVVlvdOvZ/amXHHPuD5IzRHElQn1PuoNeR6vG3s7z3Z7mS7UGewoHbC1r9/jCwi1b0Xl4iKN5SgsBFhc0Zp1bXH5+rx/sEMpEtFlyNTFTcq0elSbKZqfRAE9AUXedRAILeVL17oTjNA+mroBXYbjv9XdUuc1TrpvkhravULMHR3sYH0toqP00aBipQvBUzJJjSSfwGQMygOk=~-1~-1~-1,27524,89,-667149320,30261689-1,2,-94,-106,1,8-1,2,-94,-119,6,7,8,7,35,22,15,7,9,5,5,177,189,110,-1,2,-94,-122,0,0,0,0,1,0,0-1,2,-94,-123,-1,2,-94,-70,-1650851414;dis;,7,8;true;true;true;-480;true;24;24;true;false;-1-1,2,-94,-80,5049-1,2,-94,-116,230606057-1,2,-94,-118,217429-1,2,-94,-121,;2;5;0"
    }

    json2 = {
        "sensor_data": "7a74G7m23Vrp0o5c9083451.41-1,2,-94,-100,Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36,uaend,12147,20030107,zh-CN,Gecko,3,0,0,0,383654,9224241,1920,1040,1920,1080,1920,969,1920,,cpen:0,i1:0,dm:0,cwen:0,non:1,opc:0,fc:0,sc:0,wrc:1,isc:0,vib:1,bat:1,x11:0,x12:1,8295,0.932556441466,779634612120,loc:-1,2,-94,-101,do_en,dm_en,t_en-1,2,-94,-105,0,0,0,0,2043,630,0;-1,2,-94,-102,0,0,0,0,2043,630,0;0,0,0,0,2313,821,0;0,0,0,0,2417,937,0;1,2,0,0,2361,883,0;-1,2,-94,-108,0,2,7116,9,0,0,-1;1,1,17435,17,0,4,2460;2,2,17595,17,0,0,2460;3,1,17727,17,0,4,2460;4,1,17875,86,0,4,2460;5,2,17948,17,0,0,2460;6,2,17948,-2,0,0,2460;7,1,18691,18,0,1,-1;8,2,19596,9,0,0,2109;9,1,33950,17,0,4,2109;10,1,34021,86,0,4,2109;11,2,34086,17,0,0,2109;12,2,34101,-2,0,0,2109;-1,2,-94,-110,0,1,7022,1522,67;1,1,7032,1534,65;2,1,7048,1550,64;3,1,7065,1567,60;4,1,7082,1581,59;5,1,7098,1600,59;6,1,7116,1625,59;7,1,7132,1639,61;8,1,7149,1652,62;9,1,7165,1663,64;10,1,7182,1670,65;11,1,7198,1673,67;12,1,7215,1675,68;13,1,7235,1676,68;14,1,7251,1676,70;15,1,7275,1676,71;16,1,7283,1676,72;17,1,7298,1676,73;18,1,7315,1676,75;19,1,7332,1675,77;20,1,7380,1674,77;21,1,7395,1674,76;22,1,7403,1673,74;23,1,7415,1672,73;24,1,7431,1671,65;25,1,7448,1670,61;26,1,7464,1669,56;27,1,7481,1667,51;28,1,7499,1666,47;29,1,7515,1666,44;30,1,7531,1665,41;31,1,7548,1665,39;32,1,7565,1665,38;33,1,7582,1665,34;34,1,7599,1665,31;35,1,7616,1665,28;36,1,7633,1665,25;37,1,7649,1666,25;38,1,7666,1666,24;39,3,7732,1666,24,-1;40,4,7804,1666,24,-1;41,2,7805,1666,24,-1;42,1,7907,1660,41;43,1,7917,1653,50;44,1,7933,1645,61;45,1,7950,1632,75;46,1,7967,1614,92;47,1,7983,1595,110;48,1,8000,1565,128;49,1,8018,1529,152;50,1,8034,1481,179;51,1,8052,1428,204;52,1,8068,1337,235;53,1,8084,1268,252;54,1,8106,1201,263;55,1,8124,1135,280;56,1,8137,1078,290;57,1,8174,1039,301;58,1,8184,971,310;59,1,8202,941,315;60,1,8219,919,319;61,1,8234,903,326;62,1,8250,892,329;63,1,8269,882,331;64,1,8285,877,333;65,1,8300,873,337;66,1,8317,869,342;67,1,8333,866,346;68,1,8369,864,352;69,1,8382,864,355;70,1,8399,864,358;71,1,8416,866,362;72,1,8432,869,366;73,1,8449,874,372;74,1,8465,877,381;75,1,8482,882,388;76,1,8498,889,398;77,1,8515,897,408;78,1,8532,906,414;79,1,8549,917,427;80,1,8565,927,433;81,1,8582,934,440;82,1,8598,942,443;83,1,8616,949,447;84,1,8632,957,450;85,1,8649,965,455;86,1,8665,972,459;87,1,8683,979,465;88,1,8699,990,480;89,1,8716,996,492;90,1,8732,1002,507;91,1,8749,1002,523;92,1,8765,1002,541;93,1,8782,1002,553;94,1,8800,1002,567;95,1,8816,1000,581;96,1,8832,999,588;97,1,8849,999,593;98,1,8865,999,597;99,1,8883,995,607;100,1,8899,993,621;101,1,8916,989,639;102,1,8932,989,646;113,3,9291,984,676,2331;114,4,9380,984,676,2331;115,2,9380,984,676,2331;123,3,9820,985,684,2428;124,4,9891,985,684,2428;125,2,9893,985,684,2428;150,3,10507,992,471,2460;152,4,10581,992,471,2460;153,2,10581,992,471,2460;250,3,18166,1078,462,2477;251,4,18219,1078,462,2477;252,2,18219,1078,462,2477;366,3,33750,938,506,2109;367,4,33829,938,506,2109;368,2,33829,938,506,2109;401,3,34549,957,662,2473;402,4,34614,957,662,2473;403,2,34614,957,662,2473;454,3,36413,870,402,821;-1,2,-94,-117,-1,2,-94,-111,0,118,-1,-1,-1;-1,2,-94,-109,0,117,-1,-1,-1,-1,-1,-1,-1,-1,-1;-1,2,-94,-114,-1,2,-94,-103,3,7018;2,11464;3,16944;2,18782;3,19584;2,20598;3,30486;2,30973;3,32960;-1,2,-94,-112,https://www.nike.com/cn/-1,2,-94,-115,313818,1407891,0,118,117,0,1721942,36413,0,1559269224240,5,16680,13,455,2780,15,0,36414,1497264,0,F1462266802155339CD74F77141E0960~-1~YAAQM2UzuIE/ks1qAQAAvKawCwHc92McE7PycrDaW95RDNS6/CGfAcdG1TTJFlTjXvMyR7//o2nH35I6FIFzYdEeVVlvdOvZ/amXHHPuD5IzRHElQn1PuoNeR6vG3s7z3Z7mS7UGewoHbC1r9/jCwi1b0Xl4iKN5SgsBFhc0Zp1bXH5+rx/sEMpEtFlyNTFTcq0elSbKZqfRAE9AUXedRAILeVL17oTjNA+mroBXYbjv9XdUuc1TrpvkhravULMHR3sYH0toqP00aBipQvBUzJJjSSfwGQMygOk=~-1~-1~-1,27524,89,-667149320,30261689-1,2,-94,-106,1,8-1,2,-94,-119,6,7,8,7,35,22,15,7,9,5,5,177,189,110,-1,2,-94,-122,0,0,0,0,1,0,0-1,2,-94,-123,-1,2,-94,-70,-1650851414;dis;,7,8;true;true;true;-480;true;24;24;true;false;-1-1,2,-94,-80,5049-1,2,-94,-116,230606057-1,2,-94,-118,217429-1,2,-94,-121,;2;5;0"
    }

    print(req.cookies.get_dict())
    cookies = {
        '_abck':req.cookies.get_dict()['_abck']
    }
    url = 'https://www.nike.com/static/4fc8c9fdeb11818a5b600fe3b42865c'
    ret = req.post(url, json=json, headers=headers,cookies=cookies)
    print("第一次：", ret.json())
    print(ret.headers)
    print(req.cookies.get_dict())

    ret = req.post(url, json=json2, headers=headers)
    print("第二次：", ret.json())
    print(ret.headers)
    print(req.cookies.get_dict())

    return req


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


def check():
    url = 'https://api.nike.com/buy/checkout_previews/v2/308900b2-023b-4e80-b01b-f62d0591153e'
    json = {
        "request": {
            "email": "515788423@qq.com",
            "country": "CN",
            "currency": "CNY",
            "locale": "zh_CN",
            "channel": "SNKRS",
            "clientInfo": {
                "deviceId": "0400bpNfiPCR/AUNf94lis1ztioT9A1DShgA6/Ao2WE9gwpcE7v8aPDcWlOv5uA0UdlgclVPr2nT04dWpa2HN7KodCNhNKPIN7oLJiDbCfVZTGBk19tyNs7g8xGJ4AM/fWkjMT7M4i07wiM7RIrluaJTNZhjg11m5Ky0iz/8E93rWp/UDNqQKPsctXwB7SaH85JmyAfUMZ5LKFpm2SGEcGZ2IpvXHhwykQoiuMSNUUyGAvKLg+9aginJmamvnOVDH3SzV6i8/tb5alAK/XRNo3H5dMIK6EAX6criEeK7f1sHWr/MY6jdqwhMR1U8NguKENqeSipYNscDiy7T7W+bd9sPijjzMlk8qOA4SG4vGu6BHVn6Bt5rMAOfNh5oxVTcz01eYNlB6KRM5rkxoJRoa1a2MPPfBp8j9Zgc5euufkAbuidtn8ppbyNYRNOCPPlJnrU205+m/s9uEinvsD8Ae2HMhAjTuni0YYcF7yZHbT+hap8T0tJPmnbeZcp/aGHCqy0n6uFgohzG6tiptIXf57qiD+/NShNSOZtf1eHfkZ0HoJzSt0oGtrebhl+cErIIPd1t5JDEIMmkIq0RxtKIdel+037+7ToQ6j9QRif0QUxF+/FWC4Z0KPmWF7i03C9m3vCz5ZKQguJVBsn6yc/35JaHDFXG8dZ/+4rjjmU2L5yi9CUazeAGgOH2OW+/wThvaky9rI3MaSYrgzuOZTYvnKL0JQQ08ROukpTpxifyrThRovESnjwNVGXSgGQ8InPsuf6/kpMgG84gzO5PMQF00uJew9XqxzJ4y+q4S2EhkUn+gmCpHoNuaW8iMFyeoVK8ClD0ljAlWwXHcT/nzMar+FnRmjKx4PQbX9OHEQi+wlGoZ8X2ykV3stOnGOGu3rhaojFIr5XHrcXp6A3e7luHyq04xmEqhJPR2E4I4JJTShk9Y0R8X2Fd1ngNFGSttdZygKPcQVL2duy/r6Bk2cfD0IHAIf2vFnup4QVZyItGv9DL584iiUloUR2VuTRIAZsdlAxHLHCguNHzqNXmGR9mGYky6/GSKNklI9jLZU3Vk61yqVmuHdDU72bMGSw+Jld00Kp8oBvPA6u04i1McDaVptovbdciPTQaFQzmbybyR0SybS5mlBHKop6a4uHlWBi8fPnYDmhH8iNT5tmMPY7fFSAH5m0B4eJx8sYQo5pLMLpVT1gUUA3pDXHzRas4/GRSXiLQvkV0LESmffCJ1D3KVsetdJle8lBA/HWhRNe3VFP7yqCoe32hf+m9wrzbpErBqKdelU99UoH2xkmOMbP2hDMnxB15lwo/ksLPPFfndA3rwhwensxetClb2J9hPAXquSXzKM2zqJmU+W4xWGZYhQabfQs3h76aNh89lPir8vPX0rlCs8i9Y6lXcy00yPPfV1jYUQzq0nYSpYBqp7otoiTxlJa3c3jVldoE"
            },
            "items": [{
                "id": "f6553f15-35c2-5846-9ba3-a1b937f0b06d",
                "skuId": "d7567155-930d-5fe1-a1db-2a6c623b4c1e",
                "quantity": 1,
                "recipient": {
                    "firstName": "文强", "lastName": "林"
                },
                "shippingAddress": {
                    "address1": "2栋3单元865",
                    "address2": "东亚新干线",
                    "city": "杭州市",
                    "state": "CN-33",
                    "postalCode": "00000",
                    "county": "江干区",
                    "country": "CN"
                },
                "contactInfo": {
                    "email": "515788423@qq.com", "phoneNumber": "18968804688"
                },
                "shippingMethod": "GROUND_SERVICE"
            }]
        }
    }

    url = 'https://api.nike.com/buy/checkout_previews/v2/jobs/5e229708-f398-43fa-b273-d6df8c007b16'


def msg(name, status, content, line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


if __name__ == '__main__':
    req = requests.session()

    before(req)
    exit()
    phone = register()
