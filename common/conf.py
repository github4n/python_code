import socket

headers = {
    "duuuid": "860322734564807",
    "duplatform": "android",
    "duv": "3.2.1",
    "duloginToken": "22b45e29|30509751|b28d0fd0581af96e",
    "Cookie": "duToken=61c71f31%7C30509751%7C1548148327%7C45dd62243589e205",
}
stockx_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',

}
async_num = 200

clear_day = 60

# 开发
dev_database = {
    "host": '144.48.9.105',
    "port": 3306,
    "user": 'root',
    "passwd": 'root',
    "db": 'du',
    "charset": 'utf8',
}
dev_mongo = {
    "host": '127.0.0.1',
    "port": '27017',
    "user": '',
    "passwd": '',
}
# 线上
pro_database = {
    "host": '144.48.9.105',
    "port": 3306,
    "user": 'rank666_com',
    "passwd": 'RdPK775JrWY3Psnb',
    "db": 'rank666_com',
    "charset": 'utf8',
}
pro_mongo = {
    "host": '127.0.0.1',
    "port": '27017',
    "user": 'levislin',
    "passwd": '!!23Bayuesiri',
}

ip = socket.gethostbyname(socket.gethostname())
if ip == '127.0.0.1':
    database = pro_database
    mongo = pro_mongo
else:
    database = dev_database
    mongo = dev_mongo



# 表设置
TABLE = {
    'product': 'product',
    'sold': 'product_sold',
    'size': 'product_size',
    'token': 'lt_dollar',
    'dollar': 'lt_dollar',
    'diff': 'diff',
    'stockx': 'stockx_product_size',
    'user': 'lt_user',
    'function': 'lt_user_function',
    'taobao': 'lt_taobao',
}
