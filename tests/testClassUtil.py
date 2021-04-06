import socket
import unittest
from urllib.request import (ProxyHandler, Request, build_opener,
                            install_opener, urlopen)

import requests
import socks
from get_sd_ou.classUtil import Article, SearchPage
from sockshandler import SocksiPyHandler


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
        headers = {
                'Accept': 'application/json, text/plain, */*',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'
        }
    
        proxy_rotator = self.proxy_generator()
        global_proxies = next(proxy_rotator)
        print(global_proxies)
        # resp = requests.get('https://www.sciencedirect.com/browse/journals-and-books/', proxies=global_proxies, headers=headers)
        resp = requests.get('https://ifconfig.me/all.json', proxies=global_proxies, headers=headers)
        print(resp)
        resp.raise_for_status()
    
    def test_socks(self):

        # socks.set_default_proxy(proxy_type=socks.SOCKS5, addr="s.serverp.xyz", port=1080,
                    #   username="s1panis210", password="88890")
        
        socks.set_default_proxy(proxy_type=socks.SOCKS4, addr="110.77.135.112", port=4153)

        socket.socket = socks.socksocket
        
        default_headers = {'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"}
        req = Request('https://www.sciencedirect.com/browse/journals-and-books/', headers=default_headers)
        
        connection = urlopen(req, timeout=2)
        page_content = connection.read()
        print(page_content)
    
    def test_build_opener(self):
        opener = build_opener(SocksiPyHandler(socks.SOCKS5, "110.77.135.112", 4153))
        print (opener.open("https://www.sciencedirect.com/browse/journals-and-books/"))

    def test_urllib(self):
        proxy_support = ProxyHandler({"http":"http://154.16.202.22:3128"})
        opener = build_opener(proxy_support)
        install_opener(opener)

        html = urlopen("https://www.sciencedirect.com/browse/journals-and-books/").read()
        print(html)
    