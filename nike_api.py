import common.phone as phoneSdk
import common.randName as nameSdk

import requests, random, arrow

HOST = "https://unite.nike.com/"
HOST_S3 = "https://s3.nikecdn.com/"

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


def generateAlphanumeric(length):
    return ''.join(random.choices('0123456789abcdefABCDEF', k=length))


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


def sendPhone(req):
    url = HOST + 'phoneVerification'

    # 生成访问ID
    getVisitId()

    phone = phoneSdk.Phone.getPhone(723)

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
    code = phoneSdk.Phone.getSms(phone, 723)
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


# 设置账户信息
def setAccount(req):
    info = sendPhone(req)
    if not info:
        return False

    url = HOST_S3 + 'access/users/v1'

    # 获取姓名
    name = nameSdk.getName()

    json = {
        "country": "CN",
        "emailOnly": False,
        "firstName": name['mz'],
        "lastName": name['xm'],
        "locale": "zh_CN",
        "password": "Mn476489634",
        "receiveEmail": True,
        "registrationSiteId": "snkrsdroid",
        "registrationToken": info['token'],
        "welcomeEmailTemplate": "TSD_PROF_COMM_WELCOME_V1.0",
        "mobileNumber": "+86" + str(info['phone']),
        "receiveSms": True,
        "shoppingGender": "MENS",
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
        'Origin': 'https://s3.nikecdn.com',
        'Referer': 'https://s3.nikecdn.com/unite/mobile.html',
    }

    ret = req.post(url, params=PARAMS, json=json, headers=headers)
    print(ret.headers)
    if ret.status_code != 200:
        msg('账号设置接口异常', ret.status_code, ret.text)
        return False

    account = {
        'phone': info['phone'],
        'token': info['token'],
        'name': name['mz'] + name['xm'],
    }

    msg('账号设置成功', ret.status_code, account)

    return account


def msg(name, status, content, line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return


req = requests.session()
HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
}

phone = setAccount(req)
exit()

exit()

ret = req.get("https://unite.nike.com/session.html", headers=HEADER)
print(ret.headers)
print(ret.cookies.get_dict())

url = 'https://unite.nike.com/phoneVerification'
params = {
    'appVersion': "595",
    'experienceVersion': "493",
    'uxid': "com.nike.commerce.nikedotcom.web",
    'locale': "zh_CN",
    'backendEnvironment': "identity",
    'browser': "Google Inc.",
    'os': "undefined",
    'mobile': "false",
    'native': "false",
    'visit': "3",
    'visitor': "f282bb8b-c7f2-49ea-8f3a-5cf612a09070",
    'phoneNumber': "8618968804688",
    'country': "CN",
}
