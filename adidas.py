# 导入模块
from wxpy import *
import arrow, time

# 初始化机器人，扫码登陆
bot = Bot(cache_path=True)

mp = ensure_one(bot.search('adidasOriginals'))
# mp = ensure_one(bot.friends().search('百变'))

while True:
    city = input('请输入登记【登记城市】 例:YEEZY杭州:')
    card = input('请输入登记【身份证号】 例:33032719950518143X:')
    phone = input('请输入登记【手机号】 例：1365554789:')
    sex = input('请输入登记【性别】 例：男:')
    set_time = input('请输入开始时间 例如：15:00  24小时制：')
    sure = input('1:确认修改 2：重新修改:')
    if not sure:
        print('输入错误，请重新输入')
        continue

    if int(sure) == 1:
        break

# city = 'YEEZY杭州'
# card = '33032719950118173X'
# phone = '18968804688'
# sex = '男'
# set_time = '17:06'

time_arr = set_time.split(':')
while True:
    a = arrow.now()
    print('任务开始：等待时间   目前时间：', a.hour, ':', a.minute, ':', a.second)

    if int(a.hour) == int(time_arr[0]) and int(a.minute) == int(time_arr[1]):
        for i in range(0, 3):
            print('[发送信息]：', city)
            mp.send_msg(city)
            time.sleep(0.5)

        break
    time.sleep(0.5)


def getInfo(str):
    ret = str.find('手机号')
    ret2 = str.find('身份证号')
    ret3 = str.find('性别')
    info = {}
    if ret != -1:
        info[ret] = phone
    if ret2 != -1:
        info[ret2] = card
    if ret3 != -1:
        info[ret3] = sex

    info = sorted(info.items(), key=lambda x: x[0], reverse=False)
    arr = []
    for v in info:
        arr.append(v[1])

    final_str = ",".join(arr)

    return final_str


@bot.register(mp)
def print_group_msg(msg):
    # 回复消息内容和类型

    print('[公众号回复]：', msg.text)

    if msg.type == 'Text' and msg.text.find('身份证号') != -1:
        str = getInfo(msg.text)
        print('[发送信息]：', str)
        return str


# 堵塞线程，并进入 Python 命令行
bot.join()
