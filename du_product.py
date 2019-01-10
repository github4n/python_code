import common.conf as conf
import aiohttp, asyncio, arrow, logging, aiomysql, traceback, time

log_name = "log/du_product_log.log"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')

table_name = "stockx_product_size"
table_name2 = "product_sold"
table_name3 = "product_size"

now_time = arrow.now().timestamp


async def getData(url):
    i = 1
    while True:
        if i <= 3:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=conf.headers, timeout=60) as resp:
                            if resp.status != 200:
                                print(resp.status)
                            ret_json = await resp.json()
                            return ret_json
            except:
                print(i)
                i += 1
                traceback.print_exc()
                logging.error("[爬取错误]" + traceback.format_exc())


async def spiderList(loop, pool, page):
    try:
        # 等待返回结果
        url = 'https://stockx.com/api/browse?currency=USD&order=DESC&productCategory=sneakers&sort=most-active&page=' + str(
            page)
        data = await getData(url)
        productList = data['Products']

        # 遍历商品列表获取详情
        for v in productList:
            asyncio.ensure_future(spiderDetail(pool, v['urlKey']))
    except:
        traceback.print_exc()
        logging.error("[爬取列表] error:" + traceback.format_exc())


# 遍历商品列表获取详情
async def spiderDetail(pool, urlKey):
    try:
        logging.info("[爬取详情] product:" + str(urlKey))

        url = 'https://stockx.com/api/products/' + str(urlKey) + '?includes=market,360&currency=USD'
        product_detail = await getData(url)

        # 插入对象赋值
        size_list = product_detail['Product']['children']
        for v in size_list:
            if 'styleId' in v:
                info_arr = {
                    'title': size_list[v]['title'],
                    'styleId': size_list[v]['styleId'],
                    'shoeSize': size_list[v]['shoeSize'],
                    'year': size_list[v]['year'],
                    'imageUrl': size_list[v]['media']['imageUrl'],
                    'spiderTime': now_time,
                }
                if 'lowestAsk' in size_list[v]['market']:
                    info_arr['lowestAsk'] = size_list[v]['market']['lowestAsk']
                else:
                    info_arr['lowestAsk'] = 0
                if 'highestBid' in size_list[v]['market']:
                    info_arr['highestBid'] = size_list[v]['market']['highestBid']
                else:
                    info_arr['highestBid'] = 0
                # 等待插入
                asyncio.ensure_future(spiderInsert(pool, info_arr))
    except:
        traceback.print_exc()
        logging.error("[爬取详情] error!:" + str(traceback.format_exc()))


# 插入操作
async def spiderInsert(pool, info_arr):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # SQL 查询语句 判断是否存在
                sql_where = "SELECT * FROM " + table_name + " WHERE styleId = %s AND shoeSize = %s"
                sql_data = [info_arr['styleId'], info_arr['shoeSize']]
                await cur.execute(sql_where, sql_data)
                row = await cur.fetchone()
                if row:
                    # SQL 修改语句
                    sql_edit = "UPDATE " + table_name + " SET lowestAsk=%s," + \
                               "highestBid=%s," + \
                               "updateTime=%s " + \
                               "WHERE styleId=%s and shoeSize=%s"
                    edit_arr = [
                        info_arr['lowestAsk'],
                        info_arr['highestBid'],
                        now_time,
                        info_arr['styleId'],
                        info_arr['shoeSize'],
                    ]
                    # 修改商品
                    await cur.execute(sql_edit, edit_arr)
                else:

                    add_keys = ",".join(info_arr.keys())
                    add_vals = list(info_arr.values())
                    str = []
                    for i in range(len(add_vals)):
                        str.append("%s")
                    temp_str = ",".join(str)
                    # SQL 插入语句
                    sql = "INSERT INTO " + table_name + "(" + add_keys + ") VALUES (" + temp_str + ")"
                    # logging.info("[添加商品] 商品：" + str(info_arr['title']))
                    # 执行sql语句
                    await cur.execute(sql, add_vals)
    except:
        traceback.print_exc()
        logging.error("[处理商品] 商品：" + str(info_arr['title']) + " error:" + traceback.format_exc())


async def main(loop):
    # 等待mysql连接好
    pool = await aiomysql.create_pool(host=conf.database['host'], port=conf.database['port'],
                                      user=conf.database['user'], password=conf.database['passwd'],
                                      db=conf.database['db'], loop=loop)
    if arrow.now().hour == 13:
        for page in range(30):
            asyncio.ensure_future(spiderList(loop, pool, page))
            await asyncio.sleep(1)
    else:
        print("还没到时间，休眠 60 秒")
        time.sleep(60)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main(loop))
    loop.run_forever()
