import traceback
import common.conf as conf
import common.function as myFunc
import pymysql, arrow, logging, pymongo
# 链接mysql
db = pymysql.connect(host=conf.database['host'], port=conf.database['port'],
                     user=conf.database['user'], password=conf.database['passwd'],
                     db=conf.database['db'], charset='utf8')
cursor = db.cursor()

# 连接mongodb
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["du"]

db_diff = mydb["diff"]

db_stockx_size = mydb["stockx_size"]

db_product = mydb["du_product"]
db_size = mydb["du_size"]
db_sold = mydb["du_sold"]

# 日志配置
log_name = "log/mongo_diff.log"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')

now_time = arrow.now().timestamp
start_time = arrow.now().timestamp

# 获取美元汇率
sql = myFunc.selectSql('dollar', {'id': 1}, ['val'])
cursor.execute(sql)
dollar = cursor.fetchone()[0]

# 清空表
ret_del = db_diff.delete_many({'createTime': {'$lt': now_time}})
print("[清空集合]： ", ret_del.deleted_count)

num = 0

try:
    # 获取所有stockx数据
    ret_stockx = db_stockx_size.find({'year': {'$gt': 2018}})
    for v in ret_stockx:
        num += 1
        print("[开始查询] 第 ", num, ' 条')
        # 去除size中的特殊符号
        size = v['shoeSize'].replace('Y', '')
        size = size.replace('y', '')
        size = size.replace('K', '')
        size = size.replace('W', '')
        # 把奇怪的码数保存起来
        if size not in conf.size_conf:
            logging.info(v['styleId'] + ' ' + size)
        else:
            # 去除一些奇怪的码
            if len(size) <= 4 and float(size) < 20:
                size = conf.size_conf[size]
            else:
                size = 0

            # 查询 毒 的数据
            where = {
                'articleNumber': v['styleId'],
                'size': size,
            }
            ret_find = db_size.find_one(where)

            if ret_find is not None:
                # 获取毒的价格
                du_price = ret_find['price'] / 100
                # stockx价格
                stockx_price = round(float(v['lowestAsk']) * float(dollar), 2)
                # 获取差价
                diff = round(du_price - stockx_price, 2)
                # 如果差价在100以上
                if diff > 100 and stockx_price != 0:
                    # 获取毒的 图片 、 标题
                    ret_du = db_product.find_one({'articleNumber': v['styleId']})
                    if ret_du is None:
                        print("[无数据] ", v['styleId'], ' size：', size)
                        continue

                    # 查询这款鞋子在毒的销量
                    ret_sold = db_sold.find_one(where)
                    if ret_sold is None:
                        soldNum = 0
                    else:
                        soldNum = ret_sold['soldNum']

                    # 运费
                    freight = 100
                    # stockx 手续费
                    charge = round(13.95 * float(dollar), 1)
                    # 毒 手续费
                    du_charge = round(du_price * 0.095, 1)
                    # 纯利润
                    profit = diff - freight - charge - du_charge


                    data = {
                        'duTitle': ret_du['title'],
                        'duPrice': du_price,
                        'duSoldNum': soldNum,

                        'stockxTitle': v['title'],
                        'stockxPrice': round(stockx_price),
                        'stockxShortName': v['shortDescription'],
                        'stockxSoldNum': v['deadstockSold'],

                        'articleNumber': v['styleId'],
                        'imageUrl': ret_du['logoUrl'],
                        'diffPrice': diff,
                        'profit': profit,
                        'size': size,
                        'createTime': arrow.now().timestamp,
                        'ceil': round((float(profit) / float(stockx_price)) * 100, 2)
                    }

                    ret_diff = db_diff.insert_one(data)

                    msg = ['货号: ', v['styleId'], '名称：', ret_du['title'], ' size:', size, '纯利润:', data['profit'],' diff:', diff]
                    if ret_diff:
                        print("[插入成功]：", " ".join('%s' % id for id in msg))
                    else:
                        print("[插入失败]：", " ".join('%s' % id for id in msg))

    end_time = arrow.now().timestamp
    use_time = end_time - start_time
    msg = '总遍历: ' + str(num) + ' 总耗时: ' + str(use_time) + " 开始时间: " + str(
        arrow.get(start_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(
        arrow.get(end_time).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'))
    print(msg)
    logging.info(msg)

except:
    logging.error(traceback.format_exc())
    traceback.print_exc()
