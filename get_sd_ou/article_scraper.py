from get_sd_ou.config import Config
from get_sd_ou.classUtil import Article

with open(Config.ARTICLES_URL_PATH) as art_file:
    url_lines = art_file.readlines()

for url_line in url_lines:
    
    url = url_line.strip()
    article = Article(url)

    article_data = article.get_article_data()
    if not article_data is None:
        article_id = insert_article_data(**article_data, cnx=db_connection)