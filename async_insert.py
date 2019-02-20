import common.conf as conf
from redis_queue import RedisQueue
import time, pymysql, logging, arrow, traceback

# 日志配置
log_name = "log/async_insert.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S', filename=log_name, filemode='w')

# 链接数据库
db = pymysql.connect(host=conf.database['host'], port=conf.database['port'],
                     user=conf.database['user'], password=conf.database['passwd'],
                     db=conf.database['db'], charset='utf8')
cur = db.cursor()

q = RedisQueue('rq')

sum = 0
timeout = 0

start_time = arrow.now().timestamp

try:
    while True:
        if timeout == 180:
            msg = "超时 3 分钟 队列结束"
            logging.info(msg)
            print(msg)
            break

        result = q.get_nowait()
        if not result:
            timeout += 5
            msg = "超时 " + str(timeout) + " 秒" + " 等待获取..."
            print(msg)
            logging.info(msg)
            time.sleep(5)
            continue
        else:
            sum += 1

            msg = "第 " + str(sum) + " 条 SQL 正在执行: " + str(result)
            print(msg)
            msg = "剩余队列： " + str(q.qsize())
            print(msg)

            cur.execute(result)
except:
    traceback.print_exc()
    logging.error(traceback.format_exc())

end_time = arrow.now().timestamp
use_time = end_time - start_time

msg = "总执行：" + str(sum) + '条  总耗时: ' + str(use_time) + " 开始时间: " + str(arrow.get(start_time).format('YYYY-MM-DD HH:mm:ss')) + "  结束时间: " + str(arrow.get(end_time).format('YYYY-MM-DD HH:mm:ss'))
print(msg)
logging.info(msg)
