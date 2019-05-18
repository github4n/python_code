js = 'function ajax(url,data){' \
         'ajax=new XMLHttpRequest();' \
         'ajax.withCredentials=true;' \
         'ajax.open(\'post\',url,false);' \
         'ajax.setRequestHeader(\'content-type\',' '\'application/x-www-form-urlencoded\');' \
         'ajax.setRequestHeader(\'x-xsrf-token\',\'' + token + '\');' \
         'ajax.send(data);' \
         'return ajax.responseText' \
   '}' \
   'url=\'https://item.publish.taobao.com/taobao/manager/table.htm\';' \
   'data=\'jsonBody=%7B%22filter%22%3A%7B%22queryTitle%22%3A%22' + keyword + '%22%2C%22queryPrice%22%3A%7B%22range%22%3A%7B%22min%22%3A%22' + str(
    sprice) + '%22%2C%22max%22%3A%22' + str(
    price - 0.01) + '%22%7D%7D%2C%22querySoldQuantity%22%3A%7B%22range%22%3A%7B%22min%22%3A%22' + str(
    self.start_num) + '%22%2C%22max%22%3A%22' + str(
    self.end_num) + '%22%7D%7D%7D%2C%22pagination%22%3A%7B%22current%22%3A' + str(
    i) + '%2C%22pageSize%22%3A20%7D%2C%22table%22%3A%7B%22sort%22%3A%7B%22upShelfDate_m%22%3A%22desc%22%7D%7D%2C%22tab%22%3A%22' + status + '%22%7D\';' \
    'return ajax(url,data);'
# print(js)
while True:
    try:
        r = browser.execute_script(js)
        break
    except:
        self.logs.emit('请求失败...等待30秒后重试...')
        time.sleep(30)
j = json.loads(r)
