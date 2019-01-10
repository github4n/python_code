import requests
from bs4 import BeautifulSoup


ret = requests.get('https://www.huilv.cc/')
soup = BeautifulSoup(ret.text, "lxml")
print(soup.select(".dollar_two .back")[0].text)

