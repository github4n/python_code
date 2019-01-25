import logging


# 记录日志
def console_out(file_name, type, msg):
    ''''' Output log to file and console '''
    # Define a Handler and set a format which output to file
    logging.basicConfig(
        level=logging.DEBUG,  # 定义输出到文件的log级别，大于此级别的都被输出
        format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',  # 定义输出log的格式
        datefmt='%Y-%m-%d %A %H:%M:%S',  # 时间
        filename=file_name,  # log文件名
        filemode='w',
    )  # 写入模式“w”或“a”
    # Define a Handler and set a format which output to console
    console = logging.StreamHandler()  # 定义console handler
    console.setLevel(logging.INFO)  # 定义该handler级别
    formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')  # 定义该handler格式
    console.setFormatter(formatter)
    # Create an instance
    logging.getLogger().addHandler(console)  # 实例化添加handler

    # Print information              # 输出日志级别
    if type == 'debug':
        logging.debug(msg)
    if type == 'info':
        logging.info(msg)
    if type == 'warning':
        logging.warning(msg)
    if type == 'error':
        logging.error(msg)


# 获取插入sql
def insertSql(table_name, data_arr):
    add_keys = '(' + ",".join(data_arr.keys()) + ')'
    add_vals = list(data_arr.values())
    add_vals = '(' + ",".join('\'%s\'' % v for v in add_vals) + ')'

    # SQL 插入语句
    sql_arr = [
        'INSERT',
        'INTO',
        table_name,
        add_keys,
        'VALUES',
        add_vals,
    ]
    sql = ' '.join(sql_arr)
    return sql

# 获取查询sql
def selectSql(table_name, where={}, field=[], orderby = False, limit = False):
    if len(field) > 0:
        field_str = ",".join(field)
    else:
        field_str = '*'

    if len(where) > 0:
        where_arr = []
        for k, v in where.items():
            where_arr.append(str(k) + '=' + "'" + str(v) + "'")
        where_str = ' and '.join(where_arr)
    else:
        where_str = ''
    if orderby:
        order_str = 'ORDER BY ' + str(orderby)
    else:
        order_str = ''

    if limit:
        limit_str = 'LIMIT ' + str(limit)
    else:
        limit_str = ''

    sql_arr = [
        'SELECT',
        field_str,
        'FROM',
        table_name,
        'WHERE',
        where_str,
        order_str,
        limit_str
    ]



    sql = ' '.join(sql_arr)
    return sql

# 获取修改sql
def updateSql(table_name, update={}, where={}):
    if len(update) > 0:
        update_arr = []
        for k, v in update.items():
            update_arr.append(str(k) + '=' + "'" + str(v) + "'")
            update_str = ','.join(update_arr)
    else:
        update_str = ''
    if len(where) > 0:
        where_arr = []
        for k, v in where.items():
            where_arr.append("`" + str(k) + "`" + '=' + "'" + str(v) + "'")
        where_str = ' and '.join(where_arr)
    else:
        where_str = ''
    sql_arr = [
        'UPDATE',
        table_name,
        'SET',
        update_str,
        'WHERE',
        where_str
    ]
    sql = ' '.join(sql_arr)
    return sql
