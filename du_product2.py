import common.conf as conf
import common.function as myFunc
import pymysql, aiohttp, asyncio, hashlib, time, arrow, logging, aiomysql, traceback, json

log_name = "log/du_product_log2.log"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')

table_name = "product"
table_name2 = "product_sold"
table_name3 = "product_size"

now_time = arrow.now().timestamp


# 获取签名p
def getSign(api_params):
    hash_map = {
        "uuid": conf.headers["duuuid"],
        "platform": conf.headers["duplatform"],
        "v": conf.headers["duv"],
        "loginToken": conf.headers["duloginToken"],
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


def getApiUrl(api_url, api_params):
    url = "https://m.poizon.com"
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


async def getData(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=conf.headers, timeout=10) as resp:
            try:
                ret_json = await resp.json()
                return ret_json
            except:
                logging.error("[爬取错误]" + traceback.format_exc())


async def spiderList(pool, page):
    try:
        url = getApiUrl('/search/list', {
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
        data = await getData(url)
        productList = data['data']['productList']

        # 在获取不到商品后退出脚本
        if not productList:
            logging.info("[退出脚本] 没有产品了")
            return

        # 遍历商品列表获取详情
        for v in productList:
            asyncio.ensure_future(spiderDetail(pool, v))
    except:
        logging.error("[爬取列表] error:" + traceback.format_exc())


# 遍历商品列表获取详情
async def spiderDetail(pool, product):
    try:
        logging.info("[爬取详情] product:" + str(product['productId']))

        url = getApiUrl('/product/detail', {
            'productId': str(product['productId']),
            'isChest': str(0),
        })
        product_detail = await getData(url)

        # 插入对象赋值
        info = product_detail['data']
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
        # 等待插入
        await spiderInsert(pool, info_arr, info['sizeList'])
    except:
        logging.error("[爬取详情] error!:" + str(traceback.format_exc()))


# 添加尺码
async def insertSize(pool, size_info, product_info):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # SQL 查询语句 判断是否存在
                sql_where = myFunc.selectSql(table_name3, {
                    'productId': product_info['productId'], 'size': size_info['size']
                }, ['price', 'updateTime'])
                await cur.execute(sql_where)

                row = await cur.fetchone()
                if row:
                    # 只有更新时间小于今天凌晨的才修改
                    if row[1] < arrow.now().floor('day').timestamp:
                        price_arr = json.loads(row[0])
                        price_arr.append(size_info['item']['price'])

                        # 只保存60天价格的记录
                        while len(price_arr) > 60:
                            price_arr.pop(index=0)

                        # 修改尺码数据
                        sql_update = myFunc.updateSql(table_name3, {
                            'price': json.dumps(price_arr),
                            'updateTime': now_time,
                        }, {'productId': product_info['productId'], 'size': size_info['size']})
                        await cur.execute(sql_update)

                        logging.info('[修改尺码]' + str(product_info['productId']) + ":" + str(size_info['size']))
                else:
                    # 新增尺码数据
                    sql_insert = myFunc.insertSql(table_name3, {
                        'productId': product_info['productId'],
                        'styleId': product_info['articleNumber'],
                        'size': size_info['size'],
                        'formatSize': size_info['formatSize'],
                        'price': json.dumps([size_info['item']['price']]),
                        'spiderTime': product_info['spiderTime'],
                        'updateTime': product_info['spiderTime'],
                    })
                    await cur.execute(sql_insert)
                    logging.info('[添加尺码]' + str(product_info['productId']) + ":" + str(size_info['size']))

    except:
        traceback.print_exc()
        logging.error("[尺码处理] error:" + traceback.format_exc())


# 插入操作
async def spiderInsert(pool, info_arr, sizeList):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 只记录2018年的新款商品
                if str(info_arr['sellDate'][0:4]) != '2018':
                    return

                # 查询数据是否已经存在
                sql_where = myFunc.selectSql(table_name, {
                    'productId': info_arr['productId']
                }, ['productId', 'soldNum'])
                await cur.execute(sql_where)

                row = await cur.fetchone()
                if row:
                    # 更新已有数据
                    sql_update = myFunc.updateSql(table_name, {
                        'authPrice': info_arr['authPrice'],
                        'soldNum': info_arr['soldNum'],
                        'updateTime': info_arr['spiderTime'],
                    }, {'articleNumber': info_arr['articleNumber']})
                    await cur.execute(sql_update)

                    logging.info("[修改商品] " + sql_update)
                else:
                    # 添加商品
                    sql_insert = myFunc.insertSql(table_name, info_arr)
                    await cur.execute(sql_insert)
                    logging.info("[添加商品] " + sql_insert)


                    # 处理发售年份
                    # rep_time = info_arr['sellDate'].replace('.', '-')
                    # time_str = arrow.get(rep_time).timestamp
                    # # 计算与昨日的销售差
                    # sold_add = info_arr['soldNum'] - row[1]
                    # sql_insert = myFunc.insertSql(table_name2, {
                    #     'productId': info_arr['productId'],
                    #     'articleNumber': info_arr['articleNumber'],
                    #     'soldNum': info_arr['soldNum'],
                    #     'soldAdd': sold_add,
                    #     'spiderTime': info_arr['spiderTime'],
                    #     'sellDate': time_str,
                    # })
                    # await cur.execute(sql_insert)

                    # logging.info("[记录商品] " + sql_insert)

                # 记录各类尺码
                for v in sizeList:
                    if 'price' in v['item'] and v['item']['price'] != 0:
                        asyncio.ensure_future(insertSize(pool, v, info_arr))

    except:
        traceback.print_exc()
        logging.error("[处理商品] 商品：" + str(info_arr['title']) + " error:" + traceback.format_exc())


async def main(loop):
    # 等待mysql连接好
    pool = await aiomysql.create_pool(host=conf.database['host'], port=conf.database['port'],
                                      user=conf.database['user'], password=conf.database['passwd'],
                                      db=conf.database['db'], loop=loop)

    for page in range(400):
        asyncio.ensure_future(spiderList(pool, page))
        await asyncio.sleep(1)

    await asyncio.sleep(7200)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main(loop))
    loop.run_until_complete(task)
