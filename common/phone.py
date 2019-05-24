import requests, arrow, time, re


class Phone:
    token = '01225890449cdb9df182ecf67475f3d540a69f4b6401'
    host = 'http://api.fxhyd.cn/UserInterface.aspx'

    # 获取手机号 阿迪达斯:170 NIKE:723
    @staticmethod
    def getPhone(itemid):
        params = {
            'action': 'getmobile',
            'token': Phone.token,
            'itemid': str(itemid),
            'privince': '330000',
            'excludeno': '165',
            'timestamp': arrow.now().timestamp,
        }
        req = requests.get(Phone.host, params=params)

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
    @staticmethod
    def getSms(phone, itemid):
        params = {
            'action': 'getsms',
            'token': Phone.token,
            'itemid': str(itemid),
            'mobile': str(phone),
            'timestamp': arrow.now().timestamp,
        }
        num = 1
        while num <= 10:
            req = requests.get(Phone.host, params=params)

            if req.status_code != 200:
                print("【获取短信】接口异常")
                return False

            if req.text == '3001':
                time.sleep(10)
                num += 1
                continue

            break

        if 'success' not in req.text:
            print("【获取短信】接口失败")
            return False

        req.encoding = 'UTF-8-SIG'

        sms = req.text.split('|')[1]
        # 只获取返回值的数字
        sms = re.sub("\D", "", sms)

        print("【获取短信】：", sms)

        Phone.release(phone, itemid)

        return sms

    # 释放手机号
    @staticmethod
    def release(phone, itemid):
        params = {
            'action': 'release',
            'token': Phone.token,
            'itemid': str(itemid),
            'mobile': str(phone),
        }

        req = requests.get(Phone.host, params=params)

        if req.status_code != 200:
            print("【释放手机号】接口异常")
            return False

        if 'success' not in req.text:
            print("【释放手机号】接口失败")
            return False

        print("【释放手机号】：", phone)

        return True

    # 拉黑手机号
    def ignore(self, phone, itemid):
        params = {
            'action': 'addignore',
            'token': self.token,
            'itemid': str(itemid),
            'mobile': str(phone),
        }

        req = requests.get(self.host, params=params)

        if req.status_code != 200:
            print("【拉黑手机号】接口异常")
            return False

        if 'success' not in req.text:
            print("【拉黑手机号】接口失败")
            return False

        return True
