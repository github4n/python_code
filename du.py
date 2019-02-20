import logging
import time

import common.conf as conf
import common.function as myFunc
import hashlib
import arrow
import pymysql
import requests, traceback
import aiohttp, asyncio, aiomysql, pymysql

# header头设置
HEADERS = {
    'duuuid': '860322734564807',
    'duv': '3.2.1',
    'duplatform': 'android',
}
# 用户设置
USER = {
    'userName': '18968804688',
    'password': '9efb9f362c1d4801c254744176316b6b',
    'type': 'pwd',
    'sign': '92f338da5520da5d60403edcfb2f0867',
}
# 域名设置
URL = {
    # 域名
    'domain': 'https://du.hupu.com',
    # 登录url
    'login': '/users/unionLogin',
    # 商品列表地址
    'list': '/search/list',
    # 详情地址
    'detail': '/product/detail',
    # 尺码
    'size': '/product/lastSoldList',
}

# 商品爬取配置
PRODUCT = {
    'isSellDate': False,
    'sellDate': '2018'
}
# 当前时间设置
now_time = arrow.now().timestamp


# 登录状态测试
def tokenTest():
    i = 1
    while i <= 3:
        try:
            url = getApiUrl(URL['detail'], {
                'productId': str(9670),
                'isChest': str(0),
            })

            # 等待返回结果
            data = requests.get(url, headers=HEADERS)
            data = data.json()
            if data['status'] == 700:
                msg = "登录已失效 需要重新登录！"
                print(msg)
                logging.info(msg)
                getToken(True)
            else:
                msg = "保持登录！"
                print(msg)
                logging.info(msg)

            return
        except:
            time.sleep(5)
            print("[登录状态测试] 第 " + str(i) + ' 尝试重连URL:' + url)
            logging.error("[登录状态测试] 第 " + str(i) + ' 尝试重连URL:' + url)
            i += 1


# 获取用户登录的token
def getToken(force=False):
    try:
        db = pymysql.connect(host=conf.database['host'], port=conf.database['port'],
                             user=conf.database['user'], password=conf.database['passwd'],
                             db=conf.database['db'], charset='utf8')
        cursor = db.cursor()

        mysql_data = {}
        # 获取数据库token
        sql = myFunc.selectSql(conf.TABLE['token'], {'id': 2}, ['val', 'spiderTime'])
        cursor.execute(sql)
        ret_token = cursor.fetchone()
        # 都有数据的情况下  爬取时间不超三天则不重新登录
        if not (ret_token[1] is None) and not (ret_token[0] is None):
            mysql_data['token'] = ret_token[0]

        # 获取数据库cookie
        sql = myFunc.selectSql(conf.TABLE['token'], {'id': 3}, ['val', 'spiderTime'])
        cursor.execute(sql)
        ret_cookie = cursor.fetchone()
        # 都有数据的情况下  爬取时间不超三天则不重新登录
        if not (ret_cookie[1] is None) and not (ret_cookie[0] is None):
            mysql_data['cookie'] = ret_cookie[0]

        if 'token' in mysql_data and 'cookie' in mysql_data and not force:
            HEADERS['duloginToken'] = mysql_data['token']
            HEADERS['Cookie'] = mysql_data['cookie']
            print('获取数据库 token，cookie')
            return

        # 重置
        HEADERS['Cookie'] = ''
        HEADERS['duloginToken'] = ''
        # 重新登录
        ret = requests.post(URL['domain'] + URL['login'], data=USER, headers=HEADERS)

        if ret.status_code != 200:
            print("获取用户token失败")
            return

        ret_data = ret.json()
        if ret_data['status'] != 200:
            print(ret_data['msg'])
            return

        # 设置cookie
        HEADERS['Cookie'] = ret.headers['Set-Cookie']
        sql = myFunc.updateSql(conf.TABLE['token'], {
            'val': HEADERS['Cookie'],
            'spiderTime': now_time,
        }, {'key': 'cookie'})
        cursor.execute(sql)

        # 设置用户登录token
        HEADERS['duloginToken'] = ret_data['data']['loginInfo']['loginToken']
        sql = myFunc.updateSql(conf.TABLE['token'], {
            'val': ret_data['data']['loginInfo']['loginToken'],
            'spiderTime': now_time,
        }, {'key': 'token'})
        cursor.execute(sql)
        db.close()

        msg = "重新登录！"
        print(msg)
        logging.info(msg)
    except:
        traceback.print_exc()
        logging.error(traceback.format_exc())


# 获取签名p
def getSign(api_params):
    hash_map = {
        "uuid": HEADERS["duuuid"],
        "platform": HEADERS["duplatform"],
        "v": HEADERS["duv"],
        "loginToken": HEADERS["duloginToken"],
    }

    for k in api_params:
        hash_map[k] = api_params[k]

    hash_map = sorted(hash_map.items(), key=lambda x: x[0])

    str = ''
    for v in hash_map:
        str += v[0] + v[1]

    str += "3542e676b4c80983f6131cdfe577ac9b"

    # 生成一个md5对象
    m1 = hashlib.md5()
    # 使用md5对象里的update方法md5转换
    m1.update(str.encode("GBK"))
    sign = m1.hexdigest()
    return sign


# 生成带签名的url
def getApiUrl(api_url, api_params):
    url = URL['domain']
    # 拼接域名
    url += api_url

    # 拼接参数
    url += '?'
    for k in api_params:
        url += k + '=' + api_params[k] + '&'
    # 获取sign
    sign = getSign(api_params)
    url += 'sign=' + sign

    return url


# 组装最终访问链接
async def fetch(client, url):
    i = 1
    while i <= 3:
        try:
            async with client.get(url, headers=HEADERS, timeout=30) as res:
                assert res.status == 200
                # <coroutine object ClientResponse.text at 0x109b8ddb0>
                # 要获取HTML页面的内容, 必须在 resp.json() 前面使用 await
                res_json = await res.json()
                if res_json['status'] != 200:
                    print(res_json)
                    return
                print('URL: ', url)
                return res_json
        except:
            time.sleep(5)
            print("[尝试重连] 第 " + str(i) + ' 尝试重连URL:' + url)
            logging.error("[尝试重连] 第 " + str(i) + ' 尝试重连URL:' + url)
            i += 1


# 获取列表
async def getList(pool, client, page):
    try:
        url = getApiUrl(URL['list'], {
            "size": "[]",
            "title": "",
            "typeId": "0",
            "catId": "0",
            "unionId": "0",
            "sortType": "0",
            "sortMode": "1",
            "page": str(page),
            "limit": "20",
        })

        # 等待返回结果
        data = await fetch(client, url)
        productList = data['data']['productList']

        # 如果商品列表为空不再爬取
        if len(productList) == 0:
            return

        for v in productList:
            asyncio.ensure_future(getDetail(pool, client, v['product']['productId']))
    except:
        traceback.print_exc()
        logging.error("[爬取列表] error:" + traceback.format_exc())


# 获取商品详情
async def getDetail(pool, client, productId):
    try:

        url = getApiUrl(URL['detail'], {
            'productId': str(productId),
            'isChest': str(0),
        })
        ret_data = await fetch(client, url)

        # 插入对象赋值
        info = ret_data['data']
        info_arr = {
            'productId': info['detail']['productId'],
            'authPrice': str(info['detail']['authPrice']),
            'brandId': info['detail']['brandId'],
            'typeId': info['detail']['typeId'],
            'logoUrl': pymysql.escape_string(info['detail']['logoUrl']),
            'title': pymysql.escape_string(info['detail']['title']),
            'soldNum': info['detail']['soldNum'],
            'sellDate': info['detail']['sellDate'],
            'sizeList': info['detail']['sellDate'],
            'color': pymysql.escape_string(info['detail']['color']),
            'rapidlyExpressTips': pymysql.escape_string(info['rapidlyExpressTips']),
            'exchangeDesc': pymysql.escape_string(info['exchangeDesc']),
            'dispatchName': pymysql.escape_string(info['dispatchName']),
            'articleNumber': info['detail']['articleNumber'],
            'spiderTime': now_time,
        }

        asyncio.ensure_future(insert(pool, info_arr, info['sizeList']))

    except:
        traceback.print_exc()
        logging.error("[爬取详情] error!:" + str(traceback.format_exc()))


async def insert(pool, info_arr, sizeList):
    try:

        # 链接数据库  获取数据库游标
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 只记录2018年的新款商品
                if PRODUCT['isSellDate']:
                    if str(info_arr['sellDate'][0:4]) != '2018':
                        return

                # 查询数据是否已经存在
                sql_where = myFunc.selectSql(conf.TABLE['product'], {
                    'productId': info_arr['productId']
                }, ['productId', 'soldNum'])
                await cur.execute(sql_where)

                row = await cur.fetchone()
                if row:
                    # 更新已有数据
                    sql_update = myFunc.updateSql(conf.TABLE['product'], {
                        'authPrice': info_arr['authPrice'],
                        'soldNum': info_arr['soldNum'],
                        'updateTime': info_arr['spiderTime'],
                    }, {'articleNumber': info_arr['articleNumber']})
                    await cur.execute(sql_update)
                else:
                    # 添加商品
                    info_arr['updateTime'] = now_time
                    sql_insert = myFunc.insertSql(conf.TABLE['product'], info_arr)
                    await cur.execute(sql_insert)

                # 记录鞋子的各类尺码
                for v in sizeList:
                    if 'price' in v['item'] and v['item']['price'] != 0:
                        asyncio.ensure_future(insertSize(pool, v))
    except:
        traceback.print_exc()
        logging.error("[插入商品] error!:" + str(traceback.format_exc()))


# 记录尺码信息
async def insertSize(pool, size_info):
    try:
        articleNumber = size_info['item']['product']['articleNumber']
        # 链接数据库  获取数据库游标
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 新增尺码数据
                sql_insert = myFunc.insertSql(conf.TABLE['size'], {
                    'articleNumber': articleNumber,
                    'size': size_info['size'],
                    'formatSize': size_info['formatSize'],
                    'price': size_info['item']['price'],
                    'spiderTime': now_time,
                })
                await cur.execute(sql_insert)
    except:
        traceback.print_exc()
        logging.error("[插入尺码] error!:" + str(traceback.format_exc()))


async def main(loop):
    # 等待mysql连接好
    pool = await aiomysql.create_pool(host=conf.database['host'], port=conf.database['port'],
                                      user=conf.database['user'], password=conf.database['passwd'],
                                      db=conf.database['db'], loop=loop)

    # 建立 client request
    async with aiohttp.ClientSession() as client:
        for page in range(400):
            task = asyncio.create_task(getList(pool, client, page))
            await asyncio.sleep(3)

        done, pending = await asyncio.wait({task})

        if task in done:
            print('[爬取完成]所有爬取进程已经全部完成')
            logging.info("[爬取完成]所有爬取进程已经全部完成")


if __name__ == '__main__':
    try:
        # 获取用户token
        getToken()
        tokenTest()

        # 日志配置
        log_name = "log/du.log"
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')

        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(main(loop))
        loop.run_until_complete(task)
    except:
        logging.error(traceback.format_exc())
