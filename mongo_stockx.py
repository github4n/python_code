import common.conf as conf
import aiohttp, asyncio, arrow, logging, traceback, pymysql, pymongo
from redis_queue import RedisQueue

table_name = "stockx_product_size"
now_time = arrow.now().timestamp
# 域名
DOMAIN = 'https://stockx.com'
# 接口地址
URL = {
    # 'featured': '/api/browse?productCategory=sneakers&page=',
    'popular': '/api/browse?currency=USD&order=DESC&productCategory=sneakers&sort=most-active&page=',
    # 'newLowestAsks': '/api/browse?currency=GBP&order=DESC&productCategory=sneakers&sort=recent_asks&page=',
    # 'newHighestBids': '/api/browse?currency=USD&order=DESC&productCategory=sneakers&sort=recent_bids&page=',
    # 'averageSoldPrice': '/api/browse?order=DESC&productCategory=sneakers&sort=average_deadstock_price&page=',
    # 'totalSold': '/api/browse?productCategory=sneakers&sort=deadstock_sold&order=DESC&page=',
    # 'volatility': '/api/browse?productCategory=sneakers&sort=deadstock_sold&order=DESC&page=',
    # 'pricePremiun': '/api/browse?order=DESC&productCategory=sneakers&sort=price_premium&page=',
    # 'lastSale': '/api/browse?order=DESC&productCategory=sneakers&sort=last_sale&page=',
    # 'lowestAsk': '/api/browse?order=ASC&productCategory=sneakers&sort=lowest_ask&page=',
    # 'highestBid': '/api/browse?order=DESC&productCategory=sneakers&sort=highest_bid&page=',
    # 'releaseDate': '/api/browse?order=DESC&productCategory=sneakers&sort=release_date&page=',
}

# 连接mongodb
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["du"]
db_stockx_size = mydb["stockx_size"]

sem = asyncio.Semaphore(conf.async_num)


async def getData(client, url):
    async with sem:
        i = 1
        while i <= 3:
            try:
                async with client.get(url, headers=conf.stockx_headers, timeout=60) as resp:
                    if resp.status == 200:
                        print('URL: ', url)
                        ret_json = await resp.json()
                        return ret_json

            except:
                await asyncio.sleep(5)
                traceback.print_exc()
                print("[尝试重连] 第 " + str(i) + ' 尝试重连URL:' + url)
                logging.error("[尝试重连] 第 " + str(i) + ' 尝试重连URL:' + url)
                i += 1

        logging.error('[尝试重连] 失败！ URL:' + url)
        return False


async def spiderList(client, api_url, q):
    try:
        # 等待返回结果
        data = await getData(client, api_url)
        productList = data['Products']

        # 遍历商品列表获取详情
        for v in productList:
            asyncio.ensure_future(spiderDetail(client, v['urlKey'], q))

    except:
        traceback.print_exc()
        logging.error("[爬取列表] error:" + traceback.format_exc())


# 遍历商品列表获取详情
async def spiderDetail(client, urlKey, q):
    try:
        url = 'https://stockx.com/api/products/' + str(urlKey) + '?includes=market,360&currency=USD'
        product_detail = await getData(client, url)
        if not product_detail:
            return

        if 'Product' not in product_detail or 'children' not in product_detail['Product']:
            return

        # 插入对象赋值
        size_list = product_detail['Product']['children']
        for v in size_list:
            if 'styleId' in size_list[v]:
                info_arr = {
                    'title': pymysql.escape_string(size_list[v]['title']),
                    'styleId': size_list[v]['styleId'],
                    'shoeSize': size_list[v]['shoeSize'],
                    'year': size_list[v]['year'],
                    'shortDescription': product_detail['Product']['shortDescription'],
                    'imageUrl': pymysql.escape_string(size_list[v]['media']['imageUrl']),
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
                asyncio.ensure_future(spiderInsert(info_arr))
    except:
        traceback.print_exc()
        logging.error("[爬取详情] error!:" + str(traceback.format_exc()))


# 插入操作
async def spiderInsert(info_arr):
    try:
        where = {
            'styleId': info_arr['styleId'],
            'shoeSize': info_arr['shoeSize']
        }
        ret = db_stockx_size.find_one(where)

        if ret is None:
            # 新增数据
            ret_add = db_stockx_size.insert_one(info_arr)
            if ret_add.acknowledged:
                print("[成功插入]：", info_arr['styleId'], info_arr['shoeSize'])
            else:
                print("[ERROR 插入]：", info_arr['styleId'], info_arr['shoeSize'])

        else:
            # 判断今天是否已经爬取过   今日凌晨时间-爬取时间 > 0 则未爬取过
            is_spider = arrow.now().floor('day').timestamp - int(ret['updateTime'])
            if is_spider < 0:
                print("[已经爬取]：", info_arr['styleId'], info_arr['shoeSize'])
                return

            ret_edit = db_stockx_size.update_one(where, {'$set': {
                'lowestAsk': info_arr['lowestAsk'],
                'highestBid': info_arr['highestBid'],
                'deadstockSold': info_arr['deadstockSold'],
                'lowestAsk': info_arr['lowestAsk'],
                'updateTime': now_time,
            }})
            if ret_edit.modified_count == 1:
                print("[修改成功]：", info_arr['styleId'], info_arr['shoeSize'])
            else:
                print("没有任何修改")

    except:
        traceback.print_exc()
        logging.error("[处理商品] 商品：" + str(info_arr['title']) + " error:" + traceback.format_exc())


async def main():
    msg = "stockx 爬虫 Starting!"
    print(msg)
    logging.info(msg)

    q = RedisQueue('rq')

    # 建立 client request
    async with aiohttp.ClientSession() as client:
        for k, v in URL.items():
            for page in range(1, 25):
                api_url = DOMAIN + v + str(page)
                task = asyncio.create_task(spiderList(client, api_url, q))
                await asyncio.sleep(10)

        done, pending = await asyncio.wait({task})
        if task in done:
            print('[爬取完成]所有爬取进程已经全部完成')
            logging.info("[爬取完成]所有爬取进程已经全部完成")


if __name__ == '__main__':
    start_time = arrow.now().timestamp

    # 日志配置
    log_name = "log/mongo_stockx.log"
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='a')

    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main())
    loop.run_until_complete(task)

    end_time = arrow.now().timestamp
    use_time = end_time - start_time

    msg = '总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))
    print(msg)
    logging.info(msg)
