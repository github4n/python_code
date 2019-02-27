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
    'appos': 'web',
    'appversion': '0.1',

}
async_num = 200

# 开发
dev_database = {
    "host": '127.0.0.1',
    "port": 3306,
    "user": 'root',
    "passwd": 'root',
    "db": 'du',
    "charset": 'utf8',
}
# 线上
pro_database = {
    "host": '103.51.145.44',
    "port": 3306,
    "user": 'rank666_com',
    "passwd": 'RdPK775JrWY3Psnb',
    "db": 'rank666_com',
    "charset": 'utf8',
}

# 判断是服务器还是本机
ip = socket.gethostbyname(socket.gethostname())
if ip == '144.48.9.105':
    database = pro_database
else:
    database = dev_database

# 表设置
TABLE = {
    'product': 'product',
    'sold': 'product_sold',
    'size': 'product_size',
    'token': 'dollar',
    'dollar': 'dollar',
    'diff': 'diff',
    'stockx': 'stockx_product_size',
}

size_conf = {
    '1': '1',
    '1.5': '1.5',
    '2': '34',
    '2.5': '34.5',
    '3': '35',
    '3.5': '35.5',
    '4': '36',
    '4.5': '36.5',
    '5': '37.5',
    '5.5': '38',
    '6': '38.5',
    '6.5': '39',
    '7': '40',
    '7.5': '40.5',
    '8': '41',
    '8.5': '42',
    '9': '42.5',
    '9.5': '43',
    '10': '44',
    '10.5': '44.5',
    '11': '45',
    '11.5': '45.5',
    '12': '46',
    '12.5': '47',
    '13': '47.5',
    '13.5': '48',
    '14': '48.5',
    '14.5': '49',
    '15': '49.5',
    '15.5': '50',
    '16': '50.5',
    '16.5': '51',
    '17': '51.5',
    '17.5': '52',
    '18': '52.5',
    '18.5': '53',
    '19': '53.5',
    '19.5': '54',
    # 奇怪码
    '38': '38',
    '1616.5': '50.5',
}
