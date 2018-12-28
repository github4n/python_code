import common.conf as conf
import common.function as common
import pymysql, aiohttp, asyncio, hashlib, queue, time, sys, arrow, logging

log_name = "log/du_prodct_log.log"
# header 头
headers = {
    "duuuid": "309c23acc4953851",
    "duplatform": "android",
    "duv": "3.5.1",
    "duloginToken": "51cf4799|30509751|440810d5560dabcb",
    "Cookie": "duToken=61c71f31%7C30509751%7C1545622207%7Cfcb023622aa7d8ee",
}
# 储存product的队列
PRODUCT_Q = queue.Queue(5000)


# 获取签名p
def getSign(api_params):
    hash_map = {
        "uuid": headers["duuuid"],
        "platform": headers["duplatform"],
        "v": headers["duv"],
        "loginToken": headers["duloginToken"],
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
        async with session.get(url, headers=headers) as resp:
            try:
                ret_json = await resp.json()
                return ret_json
            except:
                common.console_out(log_name, 'error', "[爬取错误]")


async def spiderList(page):
    common.console_out(log_name, 'info', "[爬取列表] 第" + str(page) + ' 页')
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
    data = await getData(url)
    productList = data['data']['productList']
    if not productList:
        common.console_out(log_name, 'info', "[退出脚本] 没有产品了")
        sys.exit()

    for v in productList:
        url = getApiUrl('/product/detail', {
            'productId': str(v['productId']),
            'isChest': str(0),
        })
        product_detail = await getData(url)
        common.console_out(log_name, 'info', "[爬取详情] product:" + str(v['productId']))

        PRODUCT_Q.put(product_detail)
        if not PRODUCT_Q.empty():
            info = PRODUCT_Q.get()
            info = info['data']
            info_arr = [
                info['detail']['productId'],
                str(info['detail']['authPrice']),
                info['detail']['brandId'],
                info['detail']['typeId'],
                pymysql.escape_string(info['detail']['logoUrl']),
                pymysql.escape_string(info['detail']['title']),
                info['detail']['soldNum'],
                info['detail']['sellDate'],
                pymysql.escape_string(info['detail']['color']),
                info['detail']['productId'],
                pymysql.escape_string(info['rapidlyExpressTips']),
                pymysql.escape_string(info['exchangeDesc']),
                pymysql.escape_string(info['dispatchName']),
                int(time.time()),
                info['detail']['articleNumber'],
            ]
            await sqlHandle(info_arr)


async def sqlHandle(product_info):
    table_name = "product"
    table_name2 = "product_sold"
    # 打开数据库连接
    db = pymysql.connect(host=conf.database['host'], port=conf.database['port'],
                         user=conf.database['user'], passwd=conf.database['passwd'], db=conf.database['db'],
                         charset=conf.database['charset'])

    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # SQL 查询语句 判断是否存在
    sql_where = "SELECT productId,soldNum FROM " + table_name + " WHERE productId = " + str(product_info[0])
    cursor.execute(sql_where)
    row = cursor.fetchone()
    if row:
        temp = product_info.pop(0)
        product_info.append(temp)
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

        # SQL 记录商品销售数量  记录发售日期
        sold_add = product_info[5] - row[1]
        rep_time = product_info[6].replace('.', '-')
        time_str = arrow.get(rep_time).timestamp

        sold_data = [product_info[-1], product_info[5], sold_add, product_info[-3], time_str]
        sql_sold = "INSERT INTO " + table_name2 + "(productId,soldNum,soldAdd,spiderTime,sellDate) " \
                                                  "VALUES (%s,%s,%s,%s,%s)"
        try:
            common.console_out(log_name, 'info', "[修改商品]  商品：" + str(product_info[4]))
            # 执行sql语句
            cursor.execute(sql_edit, product_info)
            # 判断商品是否为2018年以后 只记录2018年新款
            if product_info[6][0:4] == '2018':
                common.console_out(log_name, 'info', "[记录商品]  商品：" + str(product_info[4]))

                cursor.execute(sql_sold, sold_data)
            # 提交到数据库执行
            db.commit()
        except:
            common.console_out(log_name, 'error', "[修改商品] " + product_info[4] + " Error!")

            # 如果发生错误则回滚
            db.rollback()
            # 关闭游标
            cursor.close()
            # 关闭数据库连接
            db.close()

        return

    # SQL 插入语句
    sql = "INSERT INTO " + table_name + "(productId,authPrice,brandId,typeId,logoUrl,title,soldNum,sellDate,color,sizeList,rapidlyExpressTips,exchangeDesc,dispatchName,spiderTime,articleNumber) " \
                                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    T = product_info

    try:
        common.console_out(log_name, 'error', "[添加商品] 商品：" + str(product_info[5]))
        # 执行sql语句
        cursor.execute(sql, T)
        # 提交到数据库执行
        db.commit()
    except:
        common.console_out(log_name, 'error', "[添加商品] 商品：" + str(product_info[5]) + " Error!")
        # 如果发生错误则回滚
        db.rollback()
        # 关闭游标
        cursor.close()
        # 关闭数据库连接
        db.close()


if __name__ == '__main__':
    page = 1
    while True:
        tasks = []
        for i in range(50):
            tasks.append(asyncio.ensure_future(spiderList(page)))
            page += 1

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*tasks))
