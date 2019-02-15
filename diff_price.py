import traceback
import du
import common.conf as conf
import common.function as myFunc
import pymysql, json, xlsxwriter, arrow,logging,asyncio,aiomysql

# 初始化excel
# filename = '对比差价' + arrow.now().format('YYYY-MM-DD') + '.xlsx'
# test_book = xlsxwriter.Workbook(filename)
# worksheet = test_book.add_worksheet('what')
# 定义起始的行列 会在这个基础上 行列各加一 作为初始行列
row = 0
col = 0

db = pymysql.connect(host=conf.database['host'], port=conf.database['port'],
                     user=conf.database['user'], password=conf.database['passwd'],
                     db=conf.database['db'], charset='utf8')


# 日志配置
log_name = "log/diff.log"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')


cursor = db.cursor()
# 清空表
sql = 'TRUNCATE TABLE diff'
cursor.execute(sql)
sql = myFunc.selectSql('dollar', {'id': 1}, ['val'])
cursor.execute(sql)
dollar = cursor.fetchone()[0]
sql = "SELECT * From stockx_product_size"
cursor.execute(sql)
rows = cursor.fetchall()
try:
    for v in rows:
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
            sql_where = myFunc.selectSql('product_size', {
                'articleNumber': v[2],
                'size': size,
            }, {}, 'spiderTime desc', 1)

            cursor.execute(sql_where)
            data = cursor.fetchone()
            if data:
                sql = myFunc.selectSql('product',{'articleNumber': v[2]}, ['title'])
                cursor.execute(sql)
                product_info = cursor.fetchone()
                # 获取毒的价格
                du_price = data[3] / 100
                # stockx价格
                stockx_price = round(float(v[6]) * float(dollar), 2)
                # print('货号：', data[7], ' size:', data[2], ' price:', price)
                # print('货号: ', v[2], ' size:', size, ' price:', round(float(v[6]) * 6.8, 2))

                diff = round(du_price - stockx_price, 2)
                # 如果差价在100以上
                if diff > 100 and stockx_price != 0:
                    # 获取毒的图片地址
                    sql_where = myFunc.selectSql(du.TABLE['product'], {'articleNumber': v[2]}, ['logoUrl'])
                    cursor.execute(sql_where)
                    ret_product = cursor.fetchone()
                    # 查询这款鞋子在毒的销量
                    sql_where = myFunc.selectSql(du.TABLE['sold'], {'articleNumber': v[2]}, ['soldNum'])
                    cursor.execute(sql_where)
                    ret_size = cursor.fetchone()
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
                        'stockxPrice': stockx_price,
                        'imageUrl': pymysql.escape_string(ret_product[0]),
                        'createTime': arrow.now().timestamp,
                        'ceil': round((float(diff) / float(stockx_price)) * 100, 2)
                    }
                    insert_sql = myFunc.insertSql('diff', data)
                    cursor.execute(insert_sql)
                    row += 1
                    print('货号: ', v[2], '名称：', v[1], ' size:', size, ' diff:', diff)
except:
    logging.info(traceback.format_exc())
    traceback.print_exc()

