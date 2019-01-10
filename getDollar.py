import common.conf as conf
import requests, pymysql
from bs4 import BeautifulSoup

ret = requests.get('https://www.huilv.cc/')
soup = BeautifulSoup(ret.text, "lxml")
print(soup.select(".dollar_two .back")[0].text)
val = soup.select(".dollar_two .back")[0].text

db = pymysql.connect(host=conf.database['host'], port=conf.database['port'],
                     user=conf.database['user'], password=conf.database['passwd'],
                     db=conf.database['db'], charset='utf8')

cursor = db.cursor()
sql = "UPDATE `dollar` SET `val`=%s WHERE (`id`='1');"
cursor.execute(sql, val)
db.close()

