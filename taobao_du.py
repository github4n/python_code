import mongo_du as du
import requests, arrow, time

# 当前时间
now_time = arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')


def login(force=False):
    where = {
        'name': 'login',
    }
    # 非强制, 使用数据库中的token
    if not force:
        ret_find = du.db_login.find_one(where)
        if ret_find:
            du.HEADERS['duloginToken'] = ret_find['loginToken']
            du.COOKIES = ret_find['cookie']
            print("更新登录状态-使用数据库数据", "成功\n", du.HEADERS)
            return True

    # 强制重新登录
    ret = requests.post(du.URL['domain'] + du.URL['login'], data=du.USER, headers=du.HEADERS)
    if ret.status_code != 200:
        print("登录接口异常")

    if ret.json()['status'] != 200:
        print("接口错误：", ret.json()['msg'])

    loginToken = ret.json()['data']['loginInfo']['loginToken']
    cookie = ret.cookies.get_dict()

    # 查询是否已经存在
    ret_find = du.db_login.update_one(where, {'$set': {
        'loginToken': loginToken,
        'cookie': cookie
    }}, upsert=True)
    if not ret_find.acknowledged:
        print("更新登录状态：", "失败！")
    else:
        print("更新登录状态:：", "成功！")

    du.HEADERS['duloginToken'] = loginToken
    du.COOKIES = ret_find['cookie']

    return True


# 访问链接
def fetch(url):
    i = 1
    while i <= 3:
        try:
            ret = requests.get(url, headers=du.HEADERS, cookies=du.COOKIES, timeout=30)

            if ret.status_code != 200:
                print("非200：", url)
                return False

            if ret.json()['status'] != 200:
                print("接口错误", ret.json()['msg'])
                login(True)
                i += 1
                continue

            return ret.json()

        except:
            print("[尝试重连] 第 " + str(i) + ' 尝试重连URL:' + url)
            time.sleep(3)
            i += 1

    return False


# 获取所有要抓取的鞋子
def getChange():
    # 去重 获取所有的商品ID
    list = du.db_change.distinct("articleNumber")
    for v in list:
        print(v)
        getDetail(v)

    return


# 获取商品详情
def getDetail(productId):
    url = du.getApiUrl(du.URL['detail'], {
        'productId': str(productId),
        'isChest': str(0),
    })

    ret_data = fetch(url)

    # 获取尺码列表
    size_list = ret_data['data']['sizeList']
    # 获取货号
    articleNumber = ret_data['data']['detail']['articleNumber']
    # 更新尺码价格
    addSize(articleNumber, size_list)


# 添加尺码
def addSize(articleNumber, size_list):
    for v in size_list:
        where = {
            'articleNumber': articleNumber,
            'size': str(v['size'])
        }

        if v['item']:
            price = v['item']['price']
            ret = du.db_price.update_one(where, {'$set': {
                'price': price,
                'updateTime': now_time,
            }}, upsert=True)

            if ret.acknowledged:
                print("更新尺码价格：", "成功", "货号：", articleNumber, 'size：', v['size'])
            else:
                print("添加尺码价格：", "成功", articleNumber, 'size：', v['size'])

    return True


if __name__ == '__main__':
    login()
    getChange()
