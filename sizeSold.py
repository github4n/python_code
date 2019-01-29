import du
import arrow, logging

now_time = arrow.now().timestamp
# 日志配置
log_name = "log/sizeSold.log"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')


# 统计数组中各个元素出现的次数
def all_list(arr):
    result = {}
    for i in set(arr):
        result[i] = arr.count(i)
    return result


# 获取尺码销量
async def getSizeSoldNum(pool, client, productInfo):
    try:
        productId = productInfo['productId']
        articleNumber = productInfo['articleNumber']
        # 链接数据库  获取数据库游标
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                url = du.getApiUrl(du.URL['size'], {
                    'productId': str(productId),
                    'lastId': '',
                    'limit': '20',
                })
                res = await du.fetch(client, url)

                # 获取数据库中尺码销量 上次爬取时间
                sql = du.myFunc.selectSql(du.TABLE['sold'], {'productId': productId}, ['updateTime'])
                await cur.execute(sql)
                ret_size = await cur.fetchone()
                if ret_size:
                    lastId = ret_size[0]
                else:
                    lastId = 0

                # 用来统计各个尺码卖出去了多少
                sizeSold = []
                # 用来统计最大的lastId
                lastId_arr = []

                # 如果还有下一页  并且获取的数据的时间小于最终爬取时间
                while res['data']['lastId'] != '' and int(res['data']['lastId']) > lastId:
                    print(res['data']['lastId'])
                    lastId_arr.append(res['data']['lastId'])
                    for v in res['data']['list']:
                        temp_size = v['item']['size']
                        sizeSold.append(temp_size)

                    url = du.getApiUrl(du.URL['size'], {
                        'productId': str(productId),
                        'lastId': res['data']['lastId'],
                        'limit': '20',
                    })

                    res = await du.fetch(client, url)

                print('articleNumber:', articleNumber, "  爬取完毕 开始统计各尺码销量")

                # 统计后的结果
                if len(sizeSold) != 0:
                    new_arr = all_list(sizeSold)
                    total = 0
                    for k, v in new_arr.items():
                        total += v
                        data = {
                            'productId': productId,
                            'articleNumber': articleNumber,
                            'size': k,
                            'soldNum': v,
                            'spiderTime': now_time,
                            'updateTime': max(lastId_arr),
                        }
                        du.asyncio.ensure_future(insertSizeSold(pool, data))

    except:
        logging.error("[尺码销量] error!:" + str(du.traceback.format_exc()))
        du.traceback.print_exc()


async def insertSizeSold(pool, data):
    try:
        # 链接数据库  获取数据库游标
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 判断数据是否已经存在
                sql = du.myFunc.selectSql(du.TABLE['sold'], {
                    'articleNumber': data['articleNumber'],
                    'size': data['size']
                }, ['soldNum'])
                await cur.execute(sql)
                row = await cur.fetchone()
                if row:
                    # 加上原来爬取的数量
                    if data['soldNum'] > 0:
                        sold = row[0] + data['soldNum']
                        sql = du.myFunc.updateSql(du.TABLE['sold'], {
                            'soldNum': sold,
                            'updateTime': data['updateTime'],
                        }, {'articleNumber': data['articleNumber'], 'size': data['size']})
                        await cur.execute(sql)

                        print("articleNumber:", data['articleNumber'], ' size: ', data['size'], 'soldNum:', row[0],
                              " add: +", data['soldNum'])
                else:
                    sql = du.myFunc.insertSql(du.TABLE['sold'], data)
                    await cur.execute(sql)

                    print("insert:", 'articleNumber:', data['articleNumber'], ' size:', data['size'], ' soldNum:', data['soldNum'])
    except:
        logging.error("[插入尺码销量] error!:" + str(du.traceback.format_exc()))
        du.traceback.print_exc()


# 获取所有商品列表
async def getAllList(pool, client):
    try:
        # 链接数据库  获取数据库游标
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = 'SELECT productId,articleNumber FROM product'
                print(sql)
                await cur.execute(sql)
                row = await cur.fetchall()

                for v in row:
                    task = du.asyncio.create_task(
                        getSizeSoldNum(pool, client, {'productId': v[0], 'articleNumber': v[1]}))
                    await du.asyncio.sleep(0.5)

                done, pending = await du.asyncio.wait({task})

                if task in done:
                    print('[主程2]所有商品列表size统计完毕')
                    du.logging.info("[主程2]所有商品列表size统计完毕")
    except:
        logging.error("[爬取详情] error!:" + str(du.traceback.format_exc()))
        du.traceback.print_exc()


async def main(loop):
    # 等待mysql连接好
    pool = await du.aiomysql.create_pool(host=du.conf.database['host'], port=du.conf.database['port'],
                                         user=du.conf.database['user'], password=du.conf.database['passwd'],
                                         db=du.conf.database['db'], loop=loop)

    # 建立 client request
    async with du.aiohttp.ClientSession() as client:
        task = du.asyncio.create_task(getAllList(pool, client))

        done, pending = await du.asyncio.wait({task})

        if task in done:
            print('[主程]所有商品列表size统计完毕')
            du.logging.info("[主程]所有商品列表size统计完毕")


if __name__ == '__main__':
    # 获取用户token
    du.getToken()

    loop = du.asyncio.get_event_loop()
    task = du.asyncio.ensure_future(main(loop))
    loop.run_until_complete(task)
