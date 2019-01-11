import common.conf as conf
import common.function as myFunc
import aiohttp, asyncio, arrow, logging, aiomysql, traceback, time

log_name = "log/du_product_log.log"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')

table_name = "stockx_product_size"
table_name2 = "product_sold"
table_name3 = "product_size"

now_time = arrow.now().timestamp


async def getData(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=conf.headers, timeout=60) as resp:
                if resp.status == 200:
                    ret_json = await resp.json()
                    return ret_json

    except:
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
        if 'children' not in product_detail['Product']:
            return
        size_list = product_detail['Product']['children']
        for v in size_list:
            if 'styleId' in size_list[v]:
                info_arr = {
                    'title': size_list[v]['title'],
                    'styleId': size_list[v]['styleId'],
                    'shoeSize': size_list[v]['shoeSize'],
                    'year': size_list[v]['year'],
                    'imageUrl': size_list[v]['media']['imageUrl'],
                    'spiderTime': now_time,
                    'updateTime': now_time,
                }
                if 'lowestAsk' in size_list[v]['market']:
                    info_arr['lowestAsk'] = size_list[v]['market']['lowestAsk']
                else:
                    info_arr['lowestAsk'] = 0
                if 'highestBid' in size_list[v]['market']:
                    info_arr['highestBid'] = size_list[v]['market']['highestBid']
                else:
                    info_arr['highestBid'] = 0
                if 'deadstockSold' in size_list[v]['market']:
                    info_arr['deadstockSold'] = size_list[v]['market']['deadstockSold']
                else:
                    info_arr['deadstockSold'] = 0
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
                sql_where = myFunc.selectSql(table_name, {
                    'styleId': info_arr['styleId'],
                    'shoeSize': info_arr['shoeSize']
                })
                # SQL 查询语句 判断是否存在
                await cur.execute(sql_where)
                row = await cur.fetchone()
                if row:
                    if row[9]:
                        update_time = row[9]
                    else:
                        update_time = 0
                    is_spider = arrow.now().floor('day').timestamp - update_time
                    # 判断今天是否已经爬取过   今日凌晨时间-爬取时间 > 0 则未爬取过
                    if is_spider > 0:
                        # 修改尺码
                        sql_update = myFunc.updateSql(table_name, {
                            'lowestAsk': info_arr['lowestAsk'],
                            'highestBid': info_arr['highestBid'],
                            'deadstockSold': info_arr['deadstockSold'],
                            'lowestAsk': info_arr['lowestAsk'],
                            'updateTime': now_time,
                        }, {'styleId': info_arr['styleId'], 'shoeSize': info_arr['shoeSize']})
                        await cur.execute(sql_update)

                        logging.info("[修改尺码] " + sql_update)
                else:
                    # 添加尺码
                    sql_insert = myFunc.insertSql(table_name, info_arr)
                    await cur.execute(sql_insert)
                    logging.info("[添加尺码] " + sql_insert)

    except:
        traceback.print_exc()
        logging.error("[处理商品] 商品：" + str(info_arr['title']) + " error:" + traceback.format_exc())


async def main(loop):
    print("开始爬虫")
    # 等待mysql连接好
    pool = await aiomysql.create_pool(host=conf.database['host'], port=conf.database['port'],
                                      user=conf.database['user'], password=conf.database['passwd'],
                                      db=conf.database['db'], loop=loop)
    for page in range(30):
        asyncio.ensure_future(spiderList(loop, pool, page))
        await asyncio.sleep(1)

    print("爬取完毕，等待 1 小时 结束脚本")
    await asyncio.sleep(3600)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main(loop))
    loop.run_until_complete(task)
