import requests
from bs4 import BeautifulSoup
import re
import csv
import json
import datetime
import time
import sys
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()
from undetected_chromedriver import Chrome,ChromeOptions
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By


class CoinMarketCapScraper:
    def __init__(self,base_url,interval):
        self.base_url = base_url
        self.interval = interval
        self.last_call = datetime.datetime.now()


    def get_page_urls(self,page_num):
        url = self.base_url+f'/?page={page_num}'

        text = self.get_selenium_page_text(url)
        soup = BeautifulSoup(text,'lxml')
        tbody = soup.find('tbody')
        tr = tbody.find_all('tr')
        data = []
        for trow in tr:
            a = trow.find_all(href=re.compile("/currencies"))
            print(a)
            a,id = a[0],a[-1]
            href = a['href']
            name = " ".join([x.text for x in a.find_all('p')])
            if len(name)<4:
                name = " ".join([x.text for x in a.find_all('span')[1:]])

            src = id.find_all('img')[0]['src']
            svg = src.split('/')[-1]
            id  = svg.split('.')[0]
            data.append([name,href,id])
        self.write_to_csv(data)


    def get_crypto_information(self,link,id):
        url = self.base_url + link + 'markets/'
        text = self.get_request(url)
        soup = BeautifulSoup(text,'lxml')
        h2 = soup.find_all('h2',attrs={"class":re.compile(" h1"),"color": "text"})
        print(h2[0])
        coin_name = h2[0].get_text(separator=' ')
        print(coin_name)
        price = soup.find_all('div',attrs={'class':re.compile('priceValue')})
        price = price[0].get_text()


        coin_slug = link.split('/')[-2]
        binance = self.find_binance_in_list(coin_slug)
        binance = "True" if binance else "False"
        max_value_price = self.get_coin_max_value(id)

        self.write_to_csv_result(coin_name,price,binance,max_value_price)



    def get_coin_max_value(self,id):
        headers = {
            'authority': 'api.coinmarketcap.com',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
            'accept': 'application/json, text/plain, */*',
            'platform': 'web',
            'x-request-id': 'ee921ed2-a719-4d07-970a-98ac64cd74b0',
            'sec-ch-ua-platform': '"Windows"',
            'origin': 'https://coinmarketcap.com',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://coinmarketcap.com/',
            'accept-language': 'en-US,en;q=0.9',
            'if-modified-since': 'Sat, 19 Mar 2022 10:06:18 GMT',
        }

        params = (
            ('id', id),
            ('range', 'ALL'),
        )

        response = self.get_request('https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/chart',headers, params)

        data = json.loads(response)
        data = data["data"]["points"]
        points = []
        for k, v in data.items():
            points.append(v['v'])
        max_val = max(points, key=lambda x: x[0])
        max_val = max_val[0]
        return max_val

    def find_binance_in_list(self,coin_slug):
        headers = {
            'authority': 'api.coinmarketcap.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
            'accept': 'application/json, text/plain, */*',
            'platform': 'web',
            'x-request-id': '447e15b6-6dac-40d9-a83c-0ecab8d77f63',
            'sec-ch-ua-platform': '"Windows"',
            'origin': 'https://coinmarketcap.com',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://coinmarketcap.com/',
            'accept-language': 'en-US,en;q=0.9',
        }

        params = (
            ('slug', coin_slug),
            ('start', '1'),
            ('limit', '100'),
            ('category', 'spot'),
            ('sort', 'cmc_rank_advanced'),
        )


        response = self.get_request('https://api.coinmarketcap.com/data-api/v3/cryptocurrency/market-pairs/latest',headers, params)
        market_pairs = json.loads(response)["data"]["marketPairs"]
        for pairs in market_pairs:
            if pairs["exchangeName"] == "Binance":
                return True
        return False



    def get_selenium_page_text(self,url):
        now = datetime.datetime.now()
        while (now - self.last_call).seconds <= self.interval:
            print("Too many calls, please wait...")
            time.sleep(5)
            now = datetime.datetime.now()
        self.last_call = now
        print("Opening Chrome Browser")
        chrome_options = ChromeOptions()

        chrome_options.headless = True

        driver = Chrome(chrome_options=chrome_options)
        print(url)
        driver.get(url)

        body = driver.find_element(By.TAG_NAME, "body")

        height = int(driver.execute_script("return document.documentElement.scrollHeight"))
        totalScrolledHeight = driver.execute_script("return window.pageYOffset + window.innerHeight")

        while totalScrolledHeight < (height - 100):
            body.send_keys(Keys.DOWN)
            height = int(driver.execute_script("return document.documentElement.scrollHeight"))
            totalScrolledHeight = driver.execute_script("return window.pageYOffset + window.innerHeight")

        text = driver.page_source
        return text


    def write_to_csv_result(self,name,price,binance,max_value_price):
        with open('coin_val.csv','a',encoding='utf-8',newline='') as file:
            csv_writer = csv.writer(file)
            rec = [name,price,binance,max_value_price,datetime.datetime.now()]
            print(rec)
            csv_writer.writerow(rec)


    def write_to_csv(self,data):
        with open('coins.csv','a',encoding='utf-8',newline='') as file:
            csv_writer = csv.writer(file)
            for each in data:
                csv_writer.writerow(each)


    def read_from_csv(self):
        with open('coins.csv', 'r', encoding='utf-8', newline='') as file:
            csv_reader = csv.reader(file)
            data=[]
            for each in csv_reader:
                data.append(each)
        return data

    def get_request(self,url,headers=[],params=[]):
        print(url)

        now = datetime.datetime.now()
        while (now - self.last_call).seconds <= self.interval:
            print("Too many calls, please wait...")
            time.sleep(5)
            now = datetime.datetime.now()
        self.last_call = now

        response = requests.get(url,headers=headers,params=params)
        print(f"Getting URL : {url}")
        print(response.status_code)
        return response.text






if __name__ == '__main__':
    base_url = "https://coinmarketcap.com"
    time_interval = 5

    c = CoinMarketCapScraper(base_url,time_interval)

    # for i in range(1,3):
    #     soup = c.get_page_urls(i)


    data = c.read_from_csv()
    for i in data:
        c.get_crypto_information(i[1],i[2])
