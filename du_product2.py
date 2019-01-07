import common.conf as conf
import pymysql, aiohttp, asyncio, hashlib, time, arrow, logging, aiomysql, traceback, json

log_name = "log/du_product_log2.log"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')

table_name = "product"
table_name2 = "product_sold"
table_name3 = "product_size"


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


async def spiderList(loop, pool, page):
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
            'spiderTime': int(time.time()),
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
                size_keys = ['productId', 'size', 'formatSize', 'price', 'spiderTime', 'updateTime']
                size_keys = ",".join(size_keys)
                # 判断尺码是否存在  并且是今天还没爬取过 储存为json方式

                # SQL 查询语句 判断是否存在
                sql_where = "SELECT price,updateTime FROM " + table_name3 + " WHERE productId = %s and size = %s"
                sql_data = [product_info['productId'], size_info['size']]
                await cur.execute(sql_where, sql_data)
                row = await cur.fetchone()

                if row:
                    # 获取今天凌晨的时间  0：00
                    today_time = arrow.now().floor('day').timestamp
                    # 只有更新时间小于今天凌晨的才修改
                    if row[1] < today_time:
                        price_arr = json.loads(row[0])
                        price_arr.append(size_info['item']['price'])

                        # 只保存60天的记录
                        while len(price_arr) > 60:
                            price_arr.pop(index=0)

                        sql_edit = "UPDATE " + table_name3 + " SET price=%s,updateTime=%s where productId = %s and size = %s"
                        sql_data = [json.dumps(price_arr), arrow.now().timestamp, product_info['productId'],
                                    size_info['size']]
                        await cur.execute(sql_edit, sql_data)

                        logging.info('[修改尺码]' + str(product_info['productId']) + ":" + str(size_info['size']))
                        logging.info("[修改尺码SQL] SELECT price FROM " + table_name3 + " WHERE productId = " + str(
                            product_info['productId']) + " and size = " + str(size_info['size']))
                else:
                    sql_size = "INSERT INTO " + table_name3 + "(" + size_keys + ") " \
                                                                                "VALUES (%s,%s,%s,%s,%s,%s)"
                    size_data = [product_info['productId'], size_info['size'], size_info['formatSize'],
                                 json.dumps([size_info['item']['price']]),
                                 product_info['spiderTime'], product_info['spiderTime']]
                    await cur.execute(sql_size, size_data)
                    logging.info('[添加尺码]' + str(product_info['productId']) + ":" + str(size_info['size']))
    except:
        traceback.print_exc()
        logging.error("[尺码处理] error:" + traceback.format_exc())


# 插入操作
async def spiderInsert(pool, info_arr, sizeList):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # SQL 查询语句 判断是否存在
                sql_where = "SELECT productId,soldNum FROM " + table_name + " WHERE productId = " + str(
                    info_arr['productId'])
                await cur.execute(sql_where)
                row = await cur.fetchone()
                if row:
                    # SQL 修改语句
                    sql_edit = "UPDATE " + table_name + " SET authPrice=%s," + \
                               "brandId=%s," + \
                               "typeId=%s," + \
                               "logoUrl=%s," + \
                               "title=%s," + \
                               "soldNum=%s," + \
                               "sellDate=%s," + \
                               "color=%s," + \
                               "sizeList=%s," + \
                               "rapidlyExpressTips=%s," + \
                               "exchangeDesc=%s," + \
                               "dispatchName=%s," + \
                               "updateTime=%s, " + \
                               "articleNumber=%s " + \
                               "WHERE productId=%s"
                    edit_arr = [
                        info_arr['authPrice'],
                        info_arr['brandId'],
                        info_arr['typeId'],
                        info_arr['logoUrl'],
                        info_arr['title'],
                        info_arr['soldNum'],
                        info_arr['sellDate'],
                        info_arr['color'],
                        info_arr['sizeList'],
                        info_arr['rapidlyExpressTips'],
                        info_arr['exchangeDesc'],
                        info_arr['dispatchName'],
                        info_arr['spiderTime'],
                        info_arr['articleNumber'],
                        info_arr['productId'],
                    ]
                    logging.info("[修改商品]  商品：" + str(info_arr['title']))
                    # 修改商品
                    await cur.execute(sql_edit, edit_arr)
                else:
                    add_keys = ",".join(info_arr.keys())
                    add_vals = list(info_arr.values())
                    # SQL 插入语句
                    sql = "INSERT INTO " + table_name + "(" + add_keys + ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                    logging.info("[添加商品] 商品：" + str(info_arr['title']))
                    # 执行sql语句
                    await cur.execute(sql, add_vals)

                if row:
                    # 单独记录2018年的新款商品
                    if str(info_arr['sellDate'][0:4]) == '2018':
                        rep_time = info_arr['sellDate'].replace('.', '-')
                        time_str = arrow.get(rep_time).timestamp
                        sold_add = info_arr['soldNum'] - row[1]
                        sold_data = [info_arr['productId'], info_arr['soldNum'], sold_add, info_arr['spiderTime'],
                                     time_str]
                        sql_sold = "INSERT INTO " + table_name2 + "(productId,soldNum,soldAdd,spiderTime,sellDate) " \
                                                                  "VALUES (%s,%s,%s,%s,%s)"
                        logging.info("[记录商品]  商品：" + str(info_arr['title']))
                        await cur.execute(sql_sold, sold_data)

                        # 记录sizelist
                        for v in sizeList:
                            if 'price' in v['item'] and v['item']['price'] != 0:
                                asyncio.ensure_future(insertSize(pool, v, info_arr))

                    return

    except Exception as e:
        traceback.print_exc()
        logging.error("[处理商品] 商品：" + str(info_arr['title']) + " error:" + traceback.format_exc())


async def main(loop):
    # 等待mysql连接好
    pool = await aiomysql.create_pool(host=conf.database['host'], port=conf.database['port'],
                                      user=conf.database['user'], password=conf.database['passwd'],
                                      db=conf.database['db'], loop=loop)

    for page in range(400):
        asyncio.ensure_future(spiderList(loop, pool, page))
        await asyncio.sleep(0.2)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main(loop))
    loop.run_until_complete(task)
