import common.function as myFunc
import common.conf as conf
import mongo_du as du
import requests, arrow, time, pymysql

# 当前时间
now_time = arrow.get(arrow.now().timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')

database = {
    "host": '144.48.9.105',
    "port": 3306,
    "user": 'rank666_com',
    "passwd": 'RdPK775JrWY3Psnb',
    "db": 'rank666_com',
    "charset": 'utf8',
}

db = pymysql.connect(host=database['host'], port=database['port'],
                     user=database['user'], password=database['passwd'],
                     db=database['db'], charset='utf8')
cursor = db.cursor(cursor=pymysql.cursors.DictCursor)


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

    # 清除token
    if 'duloginToken' in du.HEADERS:
        du.HEADERS.pop('duloginToken')

    # 强制重新登录
    ret = requests.post(du.URL['domain'] + du.URL['login'], data=du.USER, headers=du.HEADERS)
    if ret.status_code != 200:
        print("登录接口异常", "非200")
        return False

    if ret.json()['status'] != 200:
        print("登录接口错误：", ret.json())
        return False

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
    du.COOKIES = cookie

    return True


# 访问链接
def fetch(url):
    i = 1
    while i <= 1:
        try:
            ret = requests.get(url, headers=du.HEADERS, cookies=du.COOKIES, timeout=30)

            if ret.status_code != 200:
                print("非200：", url)
                return False

            if ret.json()['status'] != 200:
                print("接口错误", ret.json()['msg'])
                if ret.json()['status'] == 700:
                    print("登录过期", "开始重新登录")
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
    login()

    # 去重 获取所有的商品ID
    sql = 'SELECT DISTINCT lt_taobao.product_id FROM `lt_taobao`'
    cursor.execute(sql)
    list = cursor.fetchall()
    if not list:
        print("获取列表为空")
        return False

    for v in list:
        print("开始爬取", "商品id：", v['product_id'])
        getDetail(v['product_id'])

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
                print("更新尺码价格：", "失败", "货号：", articleNumber, 'size：', v['size'])

    return True


if __name__ == '__main__':
    getChange()

