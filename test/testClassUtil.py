import unittest

from get_sd_ou import classUtil
import requests


class TestSearchPage(unittest.TestCase):
    def test_get_articles(self):
        """
        Test that it can sum a list of integers
        """
        excpected_result = [
        'https://www.sciencedirect.com/science/article/pii/S0021925819761043',
        'https://www.sciencedirect.com/science/article/pii/S0021925819761055',
        'https://www.sciencedirect.com/science/article/pii/S0021925819761067',
        'https://www.sciencedirect.com/science/article/pii/S0021925819762802',
        'https://www.sciencedirect.com/science/article/pii/S0021925819762826',
        'https://www.sciencedirect.com/science/article/pii/S0895717710005777']

        url = "https://www.sciencedirect.com/search?date=2010&show=100"
        search_page = classUtil.SearchPage(url=url)
        result = sorted(search_page.get_articles())
        
        self.assertEqual(result[0:3] + result[-3:], excpected_result)
    
    def next_page(self):
        self.assertTrue(True)
    
    def current_page_num(self):
        self.assertTrue(True)
        return True

    def total_article_count(self):
        self.assertTrue(True)

class TestArticle(unittest.TestCase):
    def a(self):
        pass

class TestProxy(unittest.TestCase):
    def __init__(self):
        self.headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'
            }
    
    def proxy_generator(self):
        with open('proxylist.txt') as proxy_file:
            for line in proxy_file.readlines():
                yield {'http':'http'+line.strip()}

    def test_proxy(self):
        proxy_rotator = self.proxy_generator()
        global_proxies = next(proxy_rotator)
        requests.get('https://www.sciencedirect.com/browse/journals-and-books/', proxies=global_proxies, headers=self.headers)

class TestAuthor(unittest.TestCase):
    def a(self):
        pass


class TestJournalsSearch(unittest.TestCase):
    def a(self):
        pass

class TestJournal(unittest.TestCase):
    def a(self):
        pass

if __name__ == '__main__':
    unittest.main()
