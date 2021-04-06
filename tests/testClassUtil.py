import unittest

from get_sd_ou.classUtil import Article, SearchPage
import requests


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
    headers = {
                'Accept': 'application/json, text/plain, */*',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'
        }
    
    def proxy_generator(self):
        with open('proxylist.txt') as proxy_file:
            for line in proxy_file.readlines():
                yield {'http':'http'+line.strip()}

    def test_proxy(self):
        from urllib.request import build_opener, urlopen

        import socks
        import socket
        from sockshandler import SocksiPyHandler

        socks.set_default_proxy(socks.SOCKS5, "46.4.96.137", 1080)
        socket.socket = socks.socksocket
        
        default_headers = {'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"}
        
        req = Request(url, headers=default_headers)
        
        connection = urlopen(req)
        page_content = connection.read() # All requests will pass through the SOCKS proxy
        # opener = build_opener(SocksiPyHandler(socks.SOCKS5, "46.4.96.137", 1080))
        # print (opener.open("http://www.example.com/") )# All requests made by the opener will pass through the SOCKS proxy
        # proxy_rotator = self.proxy_generator()
        # global_proxies = next(proxy_rotator)
        # requests.get('https://www.sciencedirect.com/browse/journals-and-books/', proxies=global_proxies, headers=headers)
