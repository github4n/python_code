import requests, arrow, time, re

token = '01225890449cdb9df182ecf67475f3d540a69f4b6401'
host = 'http://api.fxhyd.cn/UserInterface.aspx'

# 获取手机号 阿迪达斯:170 NIKE:723

def getPhone(itemid):
    params = {
        'action': 'getmobile',
        'token': token,
        'itemid': str(itemid),
        'privince': '330000',
        'excludeno': '165',
        'timestamp': arrow.now().timestamp,
    }
    req = requests.get(host, params=params)

    if req.status_code != 200:
        print("【获取手机号】接口异常")
        return False

    if 'success' not in req.text:
        print("【获取手机号】接口失败")
        return False

    phone = req.text.split('|')[1]

    print("【获取手机号】：", phone)

    return phone

# 获取短信
def getSms(phone, itemid):
    params = {
        'action': 'getsms',
        'token': token,
        'itemid': str(itemid),
        'mobile': str(phone),
        'timestamp': arrow.now().timestamp,
    }
    print("【获取短信】：", "等待...")
    num = 1
    time_long = 10
    while num <= 12:
        req = requests.get(host, params=params)

        if req.status_code != 200:
            print("【获取短信】接口异常:", req.status_code)
            return False

        if req.text == '3001':
            print("【获取短信】:", "第 " + str(num) + " 次接收短信  " + str(num * time_long) + " 秒")

            time.sleep(time_long)
            num += 1
            continue

        break

    if 'success' not in req.text:
        release(phone,itemid)
        print("【获取短信】：", "获取超时")
        return False

    req.encoding = 'UTF-8-SIG'

    sms = req.text.split('|')[1]
    # 只获取返回值的数字
    sms = re.sub("\D", "", sms)

    print("【获取短信】：", sms)

    release(phone, itemid)

    return sms

# 释放手机号

def release(phone, itemid):
    params = {
        'action': 'release',
        'token': token,
        'itemid': str(itemid),
        'mobile': str(phone),
    }

    ret = requests.get(host, params=params)

    if ret.status_code != 200:
        print("【释放手机号】接口异常")
        return False

    if 'success' not in ret.text:
        print("【释放手机号】接口失败", ret.text)
        return False

    print("【释放手机号】：", phone)

    return True

# 拉黑手机号
def ignore(phone, itemid):
    params = {
        'action': 'addignore',
        'token': token,
        'itemid': str(itemid),
        'mobile': str(phone),
    }

    req = requests.get(host, params=params)

    if req.status_code != 200:
        print("【拉黑手机号】接口异常")
        return False

    if 'success' not in req.text:
        print("【拉黑手机号】接口失败")
        return False

    print("【拉黑手机号】：", phone)

    return True
