import logging
import socket

import socks
from bs4 import BeautifulSoup as bs

from get_sd_ou.classUtil import Article, Url
from get_sd_ou.config import Config
from get_sd_ou.databaseUtil import get_articles, init_db, insert_article_data

socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "localhost", 80)
socket.socket = socks.socksocket

url_obj = Url("https://google.com")
resp = url_obj.response

logger = logging.getLogger('mainLogger')
logger.setLevel(Config.LOG_LEVEL)

with open(Config.ARTICLES_URL_PATH) as art_file:
    url_lines = set(art_file.readlines())

db_connection = init_db()
len_articles = len(url_lines)

visited_pii = set([article['pii'] for article in get_articles(db_connection)])

skipped_count = 0

failed = []

for i, url_line in enumerate(url_lines):
    
    if i % 10 == 0:
        logger.info(f"{i}/{len_articles} | skipped: {skipped_count}")

    url = url_line.strip()
    url_obj = Url(url)
    resp = url_obj.response

    if not resp:
        if resp == 0:
            failed.append(url)
        continue
    
    soup = bs(resp, 'html.parser')
    
    del url_obj, resp

    article = Article(url, soup_data=soup)
    
    if article.pii in visited_pii:
        skipped_count += 1
        continue

    article_data = article.get_article_data()
    if not article_data is None:
        article_id = insert_article_data(**article_data, cnx=db_connection)
