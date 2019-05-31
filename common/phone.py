import requests, arrow, time, re
import logging as LOG

# 日志配置
log_name = "log/phone.log"
LOG.basicConfig(
    level=LOG.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
    filename=log_name,
    filemode='a'
)

token = '01225890449cdb9df182ecf67475f3d540a69f4b6401'
host = 'http://api.fxhyd.cn/UserInterface.aspx'


# 获取手机号 阿迪达斯:170 NIKE:723
def getPhone(itemid):
    try:
        msg('获取手机号', '等待', '正在获取...')

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
            LOG.error('获取手机号接口异常')
            return False

        if 'success' not in req.text:
            LOG.error('获取手机号接口失败')
            return False

        phone = req.text.split('|')[1]

        msg('获取手机号', '成功', phone)

        return phone
    except:
        LOG.error('获取手机号超时')
        return False


# 获取短信
def getSms(phone, itemid):
    msg('获取短信验证码', '等待', "")

    params = {
        'action': 'getsms',
        'token': token,
        'itemid': str(itemid),
        'mobile': str(phone),
        'timestamp': arrow.now().timestamp,
    }

    num = 1
    time_long = 10
    while num <= 12:
        time.sleep(time_long)

        ret = requests.get(host, params=params)

        if ret.status_code != 200:
            print("【获取短信验证码】接口异常:", ret.status_code)
            return False

        if ret.text == '3001':
            print("【获取短信验证码】:", "第 " + str(num) + " 次接收短信  " + str(num * time_long) + " 秒")
            num += 1
            continue

        break

    if 'success' not in ret.text:
        msg("获取短信验证码", "超时", '')
        release(phone, itemid)
        return False

    ret.encoding = 'UTF-8-SIG'

    sms = ret.text.split('|')[1]
    # 只获取返回值的数字
    sms = re.sub("\D", "", sms)

    msg("获取短信验证码", '成功', sms)

    release(phone, itemid)

    return sms


# 释放手机号
def release(phone, itemid):
    msg('释放手机号', '等待', '')

    params = {
        'action': 'release',
        'token': token,
        'itemid': str(itemid),
        'mobile': str(phone),
    }

    ret = requests.get(host, params=params)

    if ret.status_code != 200:
        msg('释放手机号', '接口异常', ret.status_code)
        return False

    if 'success' not in ret.text:
        msg('释放手机号', '接口失败', ret.text)
        return False


    msg('释放手机号', '成功', phone)

    return True


# 拉黑手机号
def ignore(phone, itemid):
    msg('拉黑手机号', '等待', '')

    params = {
        'action': 'addignore',
        'token': token,
        'itemid': str(itemid),
        'mobile': str(phone),
    }

    ret = requests.get(host, params=params)

    if ret.status_code != 200:
        msg('拉黑手机号', '接口异常', ret.status_code)
        return False

    if 'success' not in ret.text:
        msg('释放手机号', '接口失败', ret.text)
        return False

    msg('拉黑手机号', '成功', phone)

    return True


def msg(name, status, content, line=True):
    msg_time = arrow.get(arrow.now().timestamp).to('local').format('YYYY-MM-DD HH:mm:ss')
    print(msg_time, "[" + name + "]：", status, content)
    if line:
        print("-----------------------------------------")
    return
