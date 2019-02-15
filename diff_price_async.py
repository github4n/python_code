import traceback
import du
import common.conf as conf
import common.function as myFunc
import pymysql, arrow, logging, asyncio, aiomysql

# 日志配置
log_name = "log/diff.log"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')


async def diff(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 清空表
            sql = 'TRUNCATE TABLE diff'
            await cur.execute(sql)
            # 获取美元汇率
            sql = myFunc.selectSql(du.TABLE['dollar'], {'id': 1}, ['val'])
            await cur.execute(sql)
            ret_dollar = await cur.fetchone()
            dollar = ret_dollar[0]
            # 获取stockx的所有数据
            sql = "SELECT * From stockx_product_size"
            await cur.execute(sql)
            rows = await cur.fetchall()
            try:
                for v in rows:
                    task2 = asyncio.create_task(diff_size(pool, v, dollar))
                    await asyncio.sleep(0.1)

                done, pending = await asyncio.wait({task2})

                if task in done:
                    msg = '差价统计完成2!'
                    print(msg)
                    logging.info(msg)

            except:
                traceback.print_exc()


async def diff_size(pool, v, dollar):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 去除size中的特殊符号
            size = v[5].replace('Y', '')
            size = size.replace('y', '')
            size = size.replace('K', '')
            size = size.replace('W', '')

            # 把奇怪的码数保存起来
            if size not in conf.size_conf:
                logging.info(v[1] + ' ' + v[2] + ' ' + size)
            else:
                # 去除一些奇怪的码
                if len(size) <= 4 and float(size) < 20:
                    size = conf.size_conf[size]
                else:
                    size = 0
                # 出现38码的情况
                sql_where = myFunc.selectSql(du.TABLE['size'], {
                    'articleNumber': v[2],
                    'size': size,
                }, {}, 'spiderTime desc', 1)

                await cur.execute(sql_where)
                data = await cur.fetchone()
                if data:
                    # 获取毒商品的数据
                    sql = myFunc.selectSql(du.TABLE['product'], {'articleNumber': v[2]}, ['title'])
                    await cur.execute(sql)
                    product_info = await cur.fetchone()
                    # 毒的价格
                    du_price = data[3] / 100
                    # stockx价格
                    stockx_price = round(float(v[6]) * float(dollar), 2)
                    # 计算差价
                    diff = round(du_price - stockx_price, 2)
                    # 如果差价在100以上
                    if diff > 100 and stockx_price != 0:
                        # 获取毒的图片地址
                        sql_where = myFunc.selectSql(du.TABLE['product'], {'articleNumber': v[2]}, ['logoUrl'])
                        await cur.execute(sql_where)
                        ret_product = await cur.fetchone()
                        # 查询这款鞋子在毒的销量
                        sql_where = myFunc.selectSql(du.TABLE['sold'], {'articleNumber': v[2], 'size': size},
                                                     ['soldNum'])
                        await cur.execute(sql_where)
                        ret_size = await cur.fetchone()
                        if ret_size:
                            soldNum = ret_size[0]
                        else:
                            soldNum = 0

                        data = {
                            'articleNumber': v[2],
                            'title': pymysql.escape_string(v[1]),
                            'du_title': pymysql.escape_string(product_info[0]),
                            'diffPrice': diff,
                            'size': size,
                            'duPrice': du_price,
                            'soldNum': soldNum,
                            'xSoldNum': v[11],
                            'stockxPrice': stockx_price,
                            'imageUrl': pymysql.escape_string(ret_product[0]),
                            'createTime': arrow.now().timestamp,
                            'ceil': round((float(diff) / float(stockx_price)) * 100, 2)
                        }
                        insert_sql = myFunc.insertSql(du.TABLE['diff'], data)
                        await cur.execute(insert_sql)
                        print('货号: ', v[2], '名称：', v[1], ' size:', size, ' diff:', diff)


async def main(loop):
    # 等待mysql连接好
    pool = await aiomysql.create_pool(host=conf.database['host'], port=conf.database['port'],
                                      user=conf.database['user'], password=conf.database['passwd'],
                                      db=conf.database['db'], loop=loop)

    task = asyncio.create_task(diff(pool))

    done, pending = await asyncio.wait({task})

    if task in done:
        msg = '差价统计完成!'
        print(msg)
        logging.info(msg)


if __name__ == '__main__':
    start_time = arrow.now().timestamp
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main(loop))
    loop.run_until_complete(task)
    end_time = arrow.now().timestamp
    print("总耗时：", end_time - start_time)
