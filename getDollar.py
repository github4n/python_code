import arrow

import common.conf as conf
import common.function as myFunc
import requests, pymysql,traceback
from bs4 import BeautifulSoup

try:
    ret = requests.get('https://www.huilv.cc/')
    soup = BeautifulSoup(ret.text, "lxml")
    val = soup.select(".dollar_two .back")[0].text

    db = pymysql.connect(host=conf.database['host'], port=conf.database['port'],
                         user=conf.database['user'], password=conf.database['passwd'],
                         db=conf.database['db'], charset='utf8')

    cursor = db.cursor()
    sql = myFunc.updateSql('dollar', {'val': val, 'spiderTime': arrow.now().timestamp}, {'id': 1})
    cursor.execute(sql)
    db.close()
except:
    traceback.print_exc()
