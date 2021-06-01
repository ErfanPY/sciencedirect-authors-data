import logging
import socket

import socks
from bs4 import BeautifulSoup as bs

from get_sd_ou.classUtil import Article, Url
from get_sd_ou.config import Config
from get_sd_ou.databaseUtil import get_articles, init_db, insert_article_data

import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--proxy', help='Do use proxy or not', default=Config.USE_PROXY, action="store_true")
parser.add_argument('--path', action='store', type=str, default=Config.ARTICLES_URL_PATH, help='path to article links file.')

args = parser.parse_args()

articles_path = args.path
err_log_path = articles_path + '.failed_urls.txt'
info_log_path = articles_path + '.log'

logger = logging.getLogger('mainLogger')
logger.setLevel(Config.LOG_LEVEL)

info_handler = logging.FileHandler(info_log_path, 'w')
info_handler.setLevel(Config.LOG_LEVEL)
info_handler.setFormatter(logger.handlers[0].formatter)

logger.addHandler(info_handler)

err_handler = logging.FileHandler(err_log_path, 'a')
err_handler.setLevel(logging.ERROR)
err_handler.setFormatter(logger.handlers[0].formatter)

logger.addHandler(err_handler)


if args.proxy:
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "localhost", 8080)
    socket.socket = socks.socksocket

with open(articles_path) as art_file:
    url_lines = set(art_file.readlines())

db_connection = init_db()
len_articles = len(url_lines)

visited_pii = set([article['pii'] for article in get_articles(db_connection)])
len_visiteds = len(visited_pii)

skipped_count = 0
errors = 0
counter = 0

for i, url_line in enumerate(url_lines):
    
    if i % 10 == 0:
        logger.info(f"{articles_path} |> {i}/{len_articles} | new : {counter} | skipped: {skipped_count} | Errors: {errors} | at_start :{len_visiteds}")
    
    url = url_line.strip()

    article = Article(url)

    if article.pii in visited_pii:
        skipped_count += 1
        continue
    
   
    url_obj = Url(url)
    resp = url_obj.response

    if not resp or resp == 0:
        logger.error(url_line)
        errors += 1
        continue
    
    soup = bs(resp, 'html.parser')
    
    article._soup = soup

    del url_obj, resp

    article_data = article.get_article_data()
    if not article_data is None:
        article_id = insert_article_data(**article_data, cnx=db_connection)
        visited_pii.add(article.pii)
    
    counter += 1
