import du
import common.conf as conf
import arrow, logging as logging_size

now_time = arrow.now().timestamp



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
                sql = du.myFunc.selectSql(conf.TABLE['sold'], {'productId': productId}, ['updateTime'])
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
        logging_size.error("[尺码销量] error!:" + str(du.traceback.format_exc()))
        du.traceback.print_exc()


async def insertSizeSold(pool, data):
    try:
        # 链接数据库  获取数据库游标
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 判断数据是否已经存在
                sql = du.myFunc.selectSql(conf.TABLE['sold'], {
                    'articleNumber': data['articleNumber'],
                    'size': data['size']
                }, ['soldNum'])
                await cur.execute(sql)
                row = await cur.fetchone()
                if row:
                    # 加上原来爬取的数量
                    if data['soldNum'] > 0:
                        sold = row[0] + data['soldNum']
                        sql = du.myFunc.updateSql(conf.TABLE['sold'], {
                            'soldNum': sold,
                            'updateTime': data['updateTime'],
                        }, {'articleNumber': data['articleNumber'], 'size': data['size']})
                        await cur.execute(sql)
                        msg = "articleNumber:" + str(data['articleNumber']) + ' size: ' + str(
                            data['size']) + ' soldNum:' + str(row[0]) + " add: +" + str(data['soldNum'])
                        print(msg)
                        logging_size.info(msg)

                else:
                    sql = du.myFunc.insertSql(conf.TABLE['sold'], data)
                    await cur.execute(sql)

                    print("insert:", 'articleNumber:', data['articleNumber'], ' size:', data['size'], ' soldNum:',
                          data['soldNum'])
    except:
        logging_size.error("[插入尺码销量] error!:" + str(du.traceback.format_exc()))
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
                    logging_size.info("[主程2]所有商品列表size统计完毕")
    except:
        logging_size.error("[爬取详情] error!:" + str(du.traceback.format_exc()))
        du.traceback.print_exc()


async def main(loop):
    # 等待mysql连接好
    pool = await du.aiomysql.create_pool(host=conf.database['host'], port=conf.database['port'],
                                         user=conf.database['user'], password=conf.database['passwd'],
                                         db=conf.database['db'], loop=loop)

    # 建立 client request
    async with du.aiohttp.ClientSession() as client:
        task = du.asyncio.create_task(getAllList(pool, client))

        done, pending = await du.asyncio.wait({task})

        if task in done:
            print('[主程]所有商品列表size统计完毕')
            logging_size.info("[主程]所有商品列表size统计完毕")


if __name__ == '__main__':
    start_time = arrow.now().timestamp

    # 日志配置
    log_name = "log/sizeSold.log"
    logging_size.basicConfig(level=logging_size.DEBUG,
                             format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                             datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')
    # 获取用户token
    du.getToken()

    loop = du.asyncio.get_event_loop()
    task = du.asyncio.ensure_future(main(loop))
    loop.run_until_complete(task)

    end_time = arrow.now().timestamp
    use_time = end_time - start_time

    msg = '总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))
    print(msg)
    logging_size.info(msg)

