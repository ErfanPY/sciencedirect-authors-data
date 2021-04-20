import logging

from get_sd_ou.config import Config
from get_sd_ou.classUtil import Article
from get_sd_ou.databaseUtil import insert_article_data, init_db

logger = logging.getLogger('mainLogger')
logger.setLevel(Config.LOG_LEVEL)

with open(Config.ARTICLES_URL_PATH) as art_file:
    url_lines = art_file.readlines()

db_connection = init_db()
len_articles = len(url_lines)

for i, url_line in enumerate(url_lines):
    
    if i % 10 == 0:
        logging.info(f"{i}/{len_articles}")

    url = url_line.strip()
    article = Article(url)

    article_data = article.get_article_data()
    if not article_data is None:
        article_id = insert_article_data(**article_data, cnx=db_connection)