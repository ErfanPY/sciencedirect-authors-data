import socket
import unittest
from urllib.request import (Request, urlopen)
import urllib
import requests
import socks
from get_sd_ou.classUtil import Article, SearchPage, ProxyHandler
import get_sd_ou.classUtil

class TestSearchPage(unittest.TestCase):
    def test_get_articles(self):

        excpected_result = [
        'https://www.sciencedirect.com/science/article/pii/S0021925819761043',
        'https://www.sciencedirect.com/science/article/pii/S0021925819761055',
        'https://www.sciencedirect.com/science/article/pii/S0021925819761067',
        'https://www.sciencedirect.com/science/article/pii/S0021925819762802',
        'https://www.sciencedirect.com/science/article/pii/S0021925819762826',
        'https://www.sciencedirect.com/science/article/pii/S0895717710005777']

        url = "https://www.sciencedirect.com/search?date=2010&show=100"
        search_page = SearchPage(url=url)
        result = sorted(search_page.get_articles())
        
        self.assertEqual(result[0:3] + result[-3:], excpected_result)
    
class TestArticle(unittest.TestCase):
    def test_authorIndexError(self):
        articles = ['https://www.sciencedirect.com/science/article/pii/S1876285920300772',
            'https://www.sciencedirect.com/science/article/pii/S1876285920300802',
            'https://www.sciencedirect.com/science/article/pii/S1876285920301844',
            'https://www.sciencedirect.com/science/article/pii/S1876285920304794',
            'https://www.sciencedirect.com/science/article/pii/S1876285920304824'
            ]

        for article in articles:
            Article(article).get_article_data()

class TestProxy(unittest.TestCase):
    
    def proxy_generator(self):
        with open('get_sd_ou/proxylist.txt') as proxy_file:
            for line in proxy_file.readlines():
                yield {'http':'http://'+line.strip()}

    def test_proxy(self):
        handler = ProxyHandler("get_sd_ou/proxylist.txt")

        self.assertEqual(socket.socket.default_proxy[:2], (None, None))
        handler.rotate()
        self.assertEqual(socket.socket.default_proxy[:2], ('127.0.0.1', "1111"))
        handler.rotate()
        self.assertEqual(socket.socket.default_proxy[:2], ('127.0.0.1', "2222"))
        
        handler.set_proxy() # Clean up
    
    def test_urllib(self):
        url = "https://www.sciencedirect.com/science/article/pii/S1876285920300772"
        handler = ProxyHandler("get_sd_ou/proxylist.txt")
        handler.rotate()

        default_headers = {'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"}
        
        req = Request(url, headers=default_headers)
        
        connection = urlopen(req)
        page_content = connection.read()

    def test_proxy_list(self):
        proxy_rotator = ProxyHandler("get_sd_ou/proxylist.txt")
        url = "https://www.sciencedirect.com/science/article/pii/S1876285920300772"
        while True:
            try:
                proxy = proxy_rotator.rotate()
                default_headers = {'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"}
        
                req = Request(url, headers=default_headers)
        
                connection = urlopen(req, timeout=10)
                page_content = connection.read()
            except requests.exceptions.RequestException as e:
                # proxy_rotator.remove(proxy)
                print("Connection refused", e)
                print(f"headers={self.headers}, proxies={global_proxies}")

            except urllib.error.URLError as e:
                # proxy_rotator.remove(proxy)
                print("Connection TimeOut", e)

            else:
                self._response = resp
                