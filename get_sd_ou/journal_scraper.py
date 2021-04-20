import logging

from get_sd_ou.classUtil import Journal, JournalsSearch, Volume, Article
from queue import Queue
from threading import Thread, current_thread, Lock


from get_sd_ou.databaseUtil import insert_article_data, init_db
from get_sd_ou.config import Config

def scrape_and_save_article(article_url_queue, mysql_connection):
    first_url = article_url_queue.get()
    article_url_queue.put(first_url)

    while not article_url_queue.empty():
        url = article_url_queue.get()

        article_data, article_hash = scrape_article_url(url)
        if not article_data is None:
            save_article_to_db(article_data, mysql_connection)

            article_url_queue.task_done()
            add_to_persistance(article_hash, mysql_connection)
            logger.info(f"[{current_thread().name}] - Article scraped and saved - url = {url}")
        else:
            logger.info(f"[{current_thread().name}] skipped article: {url}")


def scrape_article_url(url):

    article = Article(url=url)
    article_hash = str(article).strip()
    if not article_hash in visited:
        article_data = article.get_article_data()

        logger.debug(f"thread: ({current_thread().name})[journal_scraper]-[scrape_article_url] | {url}")
        return article_data, article_hash
    return None, None

def save_article_to_db(article_data, db_connection):
    article_id = insert_article_data(**article_data, cnx=db_connection)
    logger.debug(f"thread: ({current_thread().name})[journal_scraper]-[save_article_to_db] | {article_id}")


def get_node_children(node, **kwargs):

    if node == "ROOT":
        yield from iterate_journal_searches(kwargs.get('start_letter', ''), kwargs.get('end_letter', 'z'))
    elif isinstance(node, JournalsSearch):
        yield from node.iterate_journals()
    elif isinstance(node, Journal):
        yield from node.iterate_volumes()
    elif isinstance(node, Volume):
        articles = node.get_articles()
        for article in articles:
            yield article
    else:
        raise Exception(f"Invalid node - ({type(node)}) - {node}")


def iterate_journal_searches(start_letter="", endletter="z"):
    while start_letter <= endletter:
        journal_search = JournalsSearch(letter=start_letter)
        while journal_search:
            yield journal_search
            journal_search = journal_search.get_next_page()
        start_letter = chr(ord(start_letter)+1)


def deep_first_search_for_articles(self_node, article_url_queue, mysql_connection, **kwargs):
    if not str(self_node) in visited:
        node_children = get_node_children(self_node, **kwargs)

        if isinstance(self_node, Volume):  # deepest node of tree before articles is Volume
            articles = list(node_children)
            a = [add_to_persistance(str(self_node).strip(), mysql_connection) for self_node in articles]
            # list(map(article_url_queue.put, articles))
        else:
            for child in node_children:
                deep_first_search_for_articles(self_node=child, article_url_queue=article_url_queue, mysql_connection=mysql_connection, **kwargs)
        add_to_persistance(str(self_node).strip(), mysql_connection)
        logger.info(f"[{current_thread().name}] Got node children: [{type(self_node)}] {str(self_node).strip()}")
    else:
        logger.info(f"[{current_thread().name}] skipped node: {str(self_node)}")



def init_persistance():
    mysql_connection = init_db()
    mysql_cursor = mysql_connection.cursor()
    results = mysql_cursor.execute("CREATE TABLE if not exists sciencedirect.visited (hash VARCHAR(512) UNIQUE);")
    mysql_connection.commit()

    print("persistance made")

    return mysql_connection
        

def add_to_persistance(item, cnx):
    lock.acquire()
    visited.add(str(item))
    lock.release()
    cursor = cnx.cursor()
    # res = cursor.execute(f"INSERT INTO sciencedirect.visited (hash) VALUES ('%s');", str(item))
    res = cursor.execute(f"INSERT IGNORE INTO sciencedirect.visited VALUES (%s);", (str(item), ))
    cnx.commit()


def write_visited(write_set, mysql_connection=None):
    res = None
    cursor = mysql_connection.cursor()
    for i in write_set:
        res = cursor.execute(f'INSERT INTO sciencedirect.visited VALUES (hash) ({str(i)});')
    mysql_connection.commit()
    
    print(res)


def load_visited(mysql_connection=None):
    cursor = mysql_connection.cursor()
    cursor.execute('SELECT hash FROM sciencedirect.visited;')
    res = [i[0] for i in cursor.fetchall()]
    return set(res)

if __name__ == "__main__":

    logger = logging.getLogger('mainLogger')
    logger.setLevel(Config.LOG_LEVEL)

    mysql_connection = init_persistance()

    file_data = load_visited(mysql_connection)
    

    visited = file_data if file_data else set()

    lock = Lock()

    article_queue = Queue(maxsize=Config.QUEUE_MAX_SIZE)
    
    start_letter = Config.START_LETTER
    end_letter   = Config.END_LETTER

    search_thread = Thread(target=deep_first_search_for_articles,
                           args=("ROOT", article_queue, mysql_connection), kwargs={"start_letter":start_letter, "end_letter":end_letter})
    try:
        search_thread.start()
        search_thread.join()
    #     for i in range(Config.THREADS_COUNT):
    #         mysql_connection = init_persistance()

    #         t = Thread(target=scrape_and_save_article, args=(article_queue, mysql_connection))
    #         t.start()

    #     article_queue.join()
    except Exception as e:
        print(e)
        print("EXCEPTION")

