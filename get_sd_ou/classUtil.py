import itertools
import json
import logging
import re
from hashlib import sha1
from urllib.parse import parse_qsl, unquote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup as bs

from get_sd_ou.config import Config

logger = logging.getLogger('mainLogger')

class ProxyHandler:
    def __init__(self, proxy_list_dir=None, proxy_type="http"):
        self.banned_proxies = []
        self.proxy_list_dir = proxy_list_dir or Config.PROXIES_DIR[proxy_type]
        self.proxy_rotator = self.proxy_rotaion_generator()

    def remove(self, proxy):
        self.banned_proxies.append(proxy)

    def rotate(self) -> None:
        proxy = next(self.proxy_rotator)

        return proxy

    def proxy_rotaion_generator(self) -> itertools.cycle:
        with open(self.proxy_list_dir) as proxy_file:
            while True:
                proxy = proxy_file.readline().strip()
                if proxy in self.banned_proxies:
                    continue
                if not proxy:
                    proxy_file.seek(0)
                yield proxy or None

proxy_rotator = ProxyHandler()

class Url():
    def __init__(self, url, headers={}, **kwargs):
        logger.debug('[ Url ] __init__ | url: %s', url)
        self.url = url
        self._response_headers = None

        if not headers:
            self.headers = {
                'Accept': 'application/json, text/plain, */*',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'
            }

        url_parts = urlparse(self.url)
        _query = frozenset(parse_qsl(url_parts.query))
        _path = unquote_plus(url_parts.path)
        self.url_parts = url_parts._replace(query=_query, path=_path)

    def join_url_path_to_self_netloc(self, url_path):
        return urljoin('https://' + self.url_parts.netloc, url_path)

    @property
    def response(self):
        if not hasattr(self, '_response'):
            while True:
                try:
                    resp = None
                    proxy_addrs = proxy_rotator.rotate()
                    proxy = 'http://' + proxy_addrs if proxy_addrs else None

                    if Config.USE_PROXY:
                        proxies = {
                        'https' : proxy,
                        }
                    else:
                        proxies = {"https": None}
                    resp = requests.get(self.url, headers=self.headers, proxies=proxies)
                    # resp = http.get(self.url, headers=self.headers)
                    resp.raise_for_status()

                except requests.exceptions.RequestException as e:
                    if not resp and resp.status_code == 404:
                        return None
                    proxy_rotator.remove(proxy)
                    print("Connection refused", e)
                    print(f"headers={self.headers}, proxies={proxy}")

                except requests.exceptions.Timeout as e:
                    proxy_rotator.remove(proxy)
                    print("Connection TimeOut", e)

                else:
                    self._response = resp
                    return self._response
                if not Config.USE_PROXY :
                    return None
        return  self._response
    def __hash__(self):
        return hash(self.url_parts[1:3])

    def __str__(self):
        return "".join(self.url_parts[1:3]).strip()

    def __bool__(self):
        return self.url and self.url != ''

class Page(Url):
    def __init__(self, url, soup_data=None, **kwargs):
        logger.debug('[ Page ] __init__ | url: %s', url)
        super().__init__(url=url, soup=None)

        self.seen_count = 0
        self.text = ''
        self._soup = None
        if soup_data:
            self._soup = soup_data

    @property
    def soup(self):
        if not self._soup is None:
            logger.debug('[ Page ] soup exist | url: %s', self.url)
            return self._soup

        url_response = self.response
        if url_response is None:
            return None
        self._soup = bs(url_response.content, 'html.parser')

        logger.debug(f'[ Page ] soup made | len_soup: {len(str(self._soup))}')
        return self._soup


class Author(dict):
    def __init__(self, first_name, last_name, id='', email='',
                 affiliation='', is_coresponde=False, do_scopus=False):

        logger.debug('[ Author ] __init__ | name: %s', first_name + last_name)
        self['first_name'] = first_name
        self['last_name'] = last_name
        self['id'] = id
        self['email'] = email
        self['affiliation'] = affiliation
        self['is_coresponde'] = is_coresponde
        if do_scopus:
            self.get_scopus()

    def get_scopus(self):
        scopus_search = 'https://www.scopus.com/results/authorNamesList.uri?sort=count-f&src=al&sid=9d5d4784ba0ec31261499d113b0fc914&sot=al&sdt=al&sl=52&s=AUTHLASTNAME%28EQUALS%28{0}%29%29+AND+AUTHFIRST%28{1}%29&st1={0}&st2={1}&orcidId=&selectionPageSearch=anl&reselectAuthor=false&activeFlag=true&showDocument=false&resultsPerPage=20&offset=1&jtp=false&currentPage=1&previousSelectionCount=0&tooManySelections=false&previousResultCount=0&authSubject=LFSC&authSubject=HLSC&authSubject=PHSC&authSubject=SOSC&exactAuthorSearch=true&showFullList=false&authorPreferredName=&origin=searchauthorfreelookup&affiliationId=&txGid=2902d9dc14a46e0e513784d44e52bc5d'
        scopus_url = Page(scopus_search.format(
            self['last_name'], self['first_name']))
        inputs = scopus_url.soup.find('input', {'id': re.compile('auid_.*')})
        if not inputs:
            return None
        self['id'] = inputs.get('value')
        return f"https://www.scopus.com/authid/detail.uri?authorId={self['id']}"

    def __str__(self) -> str:
        return self.first_name + self.last_name

    def __getattr__(self, key):
        return (self[key])


def filter_list_in_dict(dict_data, check_key, expected_value, just_first=False):
    matched_list = list(filter(lambda x: x[check_key] == expected_value, dict_data))
    if matched_list:
        return (matched_list[0] if just_first else matched_list)
    return {} if just_first else [{}, ]


class Article(Page):
    def __init__(self, url, do_bibtex=False, soup_data=None, *args, **kwargs):
        self.url = url
        self.pii = self.get_pii()

        super().__init__(url, soup_data=soup_data, *args, **kwargs)

        self.bibtex = ''
        self.bibtex_url = None

        self._title = ''
        self._keywords = ''

        if do_bibtex:
            self.bibtex = self.export_bibtex()

        self._authors = None

    def get_pii(self):
        return self.url.split('/')[-1].replace('#!', '')

    @property
    def keywords(self):
        if self._keywords:
            return self._keywords

        keywords = ''
        keywords_container = self.soup.select_one('.Keywords')
        if not keywords_container:
            return ''
        for keyword_group in keywords_container.select('.keywords-section'):
            for keyword in keyword_group.select('.keyword'):
                keywords += keyword.text + '|'

        self._keywords = keywords
        return self._keywords

    def get_article_data(self):
        """ this is the main function of article it collect all data we need from an article (needed data is specified from input)
        it get authors name and email and affiliation from article 
        """
        try:
            data = {'pii': self.pii, 'authors': self.authors, 'bibtex': self.bibtex, 'title': self.title,
                'keywords': self.keywords}
        except Exception as e:
            with open('exceptions.txt', "a") as excp_file:
                excp_file.write(f"\n[519], url:{self.url}, exception:{e}\n")
            print(self.url)
            raise e

        return data

    def export_bibtex(self):
        self.bibtex_url = Url(
            f'https://www.sciencedirect.com/sdfe/arp/cite?pii={self.pii}&format=text/x-bibtex&wi')
        self.bibtex_file_path = f'articles/{self.pii}.bib'
        with open(self.bibtex_file_path, 'ab') as f:
            f.write(http.get(self.bibtex_url, headers=self.headers))
        return self.bibtex_url

    @staticmethod
    def _author_icons(tag_a):
        is_coresponde = bool(tag_a.select('.icon-person'))
        has_email = bool(tag_a.select('.icon-envelope'))
        return {'has_email': has_email, 'is_coresponde': is_coresponde}

    def _author_from_json(self):
        logger.debug('[class] [Article] getting authors from json')
        json_element = self.soup.find_all(
            'script', {'type': "application/json"})[0].contents[0]
        json_data = json.loads(str(json_element))

        authors_res = {}
        authors_list_json = []

        authors_groups_list_json = json_data['authors']['content']
        authors_groups_list_json = list(
            filter(lambda dict: dict['#name'] == 'author-group', authors_groups_list_json))

        for group in authors_groups_list_json:  # in authors maybe some group which devides authors
            group_authors = list(
                filter(lambda dict: dict['#name'] == 'author', group['$$']))
            [authors_list_json.append(group_author) for group_author in group_authors]

        affiliations_data_dict = json_data['authors']['affiliations']
        for index, author_json in enumerate(authors_list_json):
            reference_list = list(filter(lambda dict: dict['#name'] == 'cross-ref', author_json['$$']))
            affiliations_id_list = [ref['$']['refid'] for ref in reference_list if 'aff' in ref['$']['refid']]
            affiliation_text = ''
            for affiliation_id in affiliations_id_list:
                affiliation_json = affiliations_data_dict.get(affiliation_id)
                
                if affiliation_json is None:
                    continue

                affiliation_fn = list(filter(lambda dict: dict['#name'] == 'textfn', affiliation_json['$$']))[0]
                if affiliation_fn.get('$$'):
                    affiliation_text_list = list(filter(lambda dict: dict['#name'] == '__text__', affiliation_fn['$$']))
                    for affiliation_text_item in affiliation_text_list:
                        affiliation_text += affiliation_text_item['_'] + '||'
                else:
                    affiliation_text += affiliation_fn['_'] + '||'

            first_name = filter_list_in_dict(author_json['$$'], '#name', 'given-name', just_first=True).get('_',
                                                                                                            'noFirstName')
            last_name = filter_list_in_dict(author_json['$$'], '#name', 'surname', just_first=True).get('_',
                                                                                                        'noLastName')
            email_check = filter_list_in_dict(author_json['$$'], '#name', 'e-address', just_first=True)
            try:
                email = email_check['_'] if email_check else None
            except KeyError as e:
                with open('exceptions.txt', "a") as excp_file:
                    excp_file.write(f"\n[519], url:{self.url}, exception:{e}\n")
                email = email_check['$$'][0]['_']

            authors_res[index] = {'first_name': first_name, 'last_name': last_name,
                                  'email': email, 'affiliation': affiliation_text}
        return authors_res

    @property
    def authors(self):
        logger.debug('[class] [Article] getting authors')
        if not self._authors:
            elements = self.soup.select_one('#author-group').find_all('a')
            authors_data = self._author_from_json()
            for index, author_element in enumerate(elements[:len(authors_data)]):
                icons = self._author_icons(author_element)
                try:
                    authors_data[index]['is_coresponde'] = icons['is_coresponde']
                except KeyError as e:
                    authors_data[index]['is_coresponde'] = False
                logger.debug('Author got, %s', authors_data[index])

            authors_objects = [Author(**author_data)
                               for author_data in authors_data.values()]
            self._authors = authors_objects
            logger.debug('[ Article ] authors: %s', self._authors)
        return self._authors

    @property
    def title(self):
        if self._title is None:
            title_box = self.soup.select_one('.title-text')
            if title_box is None:
               title_box = self.soup.select_one(".reference")
            self._title = title_box.text
        return self._title


class SearchPage(Page):
    def __init__(self, url='', show_per_page=100, start_offset=0, soup_data=None, **search_kwargs):
        if not url:
            url = 'https://www.sciencedirect.com/search?'
            for key, value in search_kwargs.items():
                if value:
                    url += '{}={}&'.format(key, value)
            url += 'show={}&'.format(show_per_page)

        logger.debug('[ SearchPage ] __init__ | url: %s', url)
        super().__init__(url, soup_data=soup_data)

        self.url = url
        self.query = dict(self.url_parts.query)
        self.search_kwargs = self.query
        self.show_per_page = show_per_page
        self.offset = self.query.get('offset', start_offset)
        self.offset = self.offset if self.offset != '' else 0
        self.search_kwargs['offset'] = self.offset


    def get_articles(self):
        logger.debug('[ SearchPage ] getting articles | url: %s', self.url)
        if self.soup is None:
            return []
        search_result = self.soup.find_all('a')
        articles = []
        for article in search_result:
            if article.get('href'):
                article_link = article.get('href')
                if 'pii' in article_link and not 'pdf' in article_link and not (
                        article_link.split('/')[-1].startswith('B')):
                    articles.append(
                        urljoin('https://' + self.url_parts.netloc, article_link))
                    logger.debug(
                        '[ SearchPage ] one article added | url: %s', self.url)
        logger.debug('[ SearchPage ] all articles got | url: %s', self.url)
        return articles

    @property
    def current_page_num(self):
        if not hasattr(self, '_current_page_num'):
            page_courser_text = self.soup.select_one(
                '#srp-pagination > li:nth-child(1)').text
            if page_courser_text == 'previous':
                page_courser_text = self.soup.select_one('#srp-pagination > li:nth-child(2)').text
            self._current_page_num = int(page_courser_text.split(' ')[1])
        return self._current_page_num

    @property
    def pages_count(self):
        if not hasattr(self, '_pages_count'):
            page_courser_text = self.soup.select_one(
                '#srp-pagination > li:nth-child(1)').text
            if page_courser_text == 'previous':
                page_courser_text = self.soup.select_one('#srp-pagination > li:nth-child(2)').text
            self._pages_count = int(page_courser_text.split(' ')[-1])
        return self._pages_count

    @property
    def total_article_count(self):
        if not hasattr(self, '_total_article_count'):
            self._total_article_count = self.pages_count * self.show_per_page
        return self._total_article_count

    def next_page(self):
        next_url = self.soup.select_one('li.next-link > a')
        try:
            href = next_url.get('href')
            return SearchPage(urljoin('https://' + self.url_parts.netloc, href))
        except AttributeError as e:
            with open('exceptions.txt', "a") as excp_file:
                excp_file.write(f"\n[519], url:{self.url}, exception:{e}\n")
            return None


class Volume(SearchPage):
    def __init__(self, url, **kwargs):
        super().__init__(url=url, **kwargs)

    def get_previous(self):
        soup = self.soup
        if soup is None:
            return None
        
        previous_volume = soup.select_one('.u-padding-xs-hor > div:nth-child(1) > a:nth-child(1)')
        
        if previous_volume is None:
            return None
        
        return previous_volume.get('href', False)


class Journal(Page):
    def __init__(self, url='', journal_name='', page_kwargs={}, **kwargs):
        logger.debug('[ SearchPage ] __init__ | url: %s', url)
        super().__init__(url, **kwargs)
        if not url:
            url = 'https://www.sciencedirect.com/journal/{journal_name}/articles-in-press?'

            for key, value in page_kwargs.items():
                if value:
                    url += '{}={}&'.format(key, value)

        self.url = url
        self.page_kwargs = page_kwargs
        self.kwargs = kwargs
        self.query = dict(self.url_parts.query)
        self.search_kwargs = self.query
        self.page = self.query.get('page')
        self.page = self.page if self.page != '' else 1
        self.search_kwargs['page'] = self.page
        # self.journal_name = journal_name if journal_name else self.soup.select_one('.anchor-text').text


    def iterate_volumes(self):
        last_issue_url = self.get_last_issue_url()
        if not last_issue_url is None:
            last_issue = Volume(url=last_issue_url)
            
            if last_issue.response is None :
                return []

            yield last_issue
            previous_issue_url = ''
            previous_issue_path = last_issue.get_previous()

            while previous_issue_path:
                previous_issue_url = self.join_url_path_to_self_netloc(previous_issue_path)
                previous_issue = Volume(url=previous_issue_url)

                yield previous_issue
                previous_issue_path = previous_issue.get_previous()
        else:
            return []
        return []

    def get_last_issue_url(self):
        # Sciencedirect return last issue url whene requests outof boundry issue number
        last_issue_url = self.url + "/vol/1000000000000"
        return last_issue_url


    @property
    def current_page_num(self):
        if not hasattr(self, '_current_page_num'):
            page_courser_text = self.soup.select_one('pagination-pages-label').text
            self._current_page_num = int(page_courser_text.split('of')[0].split('page')[-1])
        return self._current_page_num

    @property
    def pages_count(self):
        if not hasattr(self, '_pages_count'):
            page_courser_text = self.soup.select_one('pagination-pages-label').text
            self._pages_count = int(page_courser_text.split('of')[-1])
        return self._pages_count

    # def next_page(self):
    #     if self.current_page_num < self.pages_count:
    #         next_journal = Journal(journal_name=self.journal_name, page_kwargs={'page': self.current_page_num + 1},
    #                                **self.kwargs)
    #         return next_journal.url


class JournalsSearch(Page):
    def __init__(self, url='', letter='', start_page=1, soup_data=None, **search_kwargs):
        if not url:
            url = f'https://www.sciencedirect.com/browse/journals-and-books/{letter}?'
            if start_page != 1: search_kwargs['page'] = start_page
            for key, value in search_kwargs.items():
                if value:
                    url += '{}={}&'.format(key, value)

        logger.debug('[ SearchPage ] __init__ | url: %s', url)
        super().__init__(url, soup_data=soup_data)

        self.url = url
        self.letter = letter
        self.query = dict(self.url_parts.query)
        self.search_kwargs = self.query
        self.page_num = self.query.get('page', start_page)
        self.page_num = int(self.page_num) if self.page_num != '' else 1
        self.search_kwargs['page'] = self.page_num
        self._pages_count = None

    def iterate_journals(self):
        journals = self._get_page_journals(self)
        for journal in journals:
            yield Journal(journal)
        next_journal_search_page = self.get_next_page()

        while next_journal_search_page:
            next_journals = next_journal_search_page._get_page_journals(next_journal_search_page)
            for next_journal in next_journals:
                yield Journal(next_journal)
            next_journal_search_page = next_journal_search_page.get_next_page()

    @staticmethod
    def _get_page_journals(journal_search_page):
        journals_list_div = journal_search_page.soup.select_one("#publication-list")
        search_result = journals_list_div.find_all('a')
        journals = []

        for journal in search_result:
            journal_path = journal.get('href')
            if any([check in journal_path for check in ['handbook', 'journal', 'bookseries']]):
                journals.append(urljoin('https://' + journal_search_page.url_parts.netloc, journal_path))

        return journals

    def get_next_page(self):
        if self.page_num < self.pages_count:
            return JournalsSearch(letter=self.letter, start_page=self.page_num + 1, **self.search_kwargs)
        return False

    @property
    def pages_count(self):
        try:
            if self._pages_count is None:
                page_counter_text = self.soup.select_one('.pagination-pages-label').text
                self._pages_count = int(page_counter_text.split('of')[-1])
        except Exception as e:
            with open('exceptions.txt', "a") as excp_file:
                excp_file.write(f"\n[519], url:{self.url}, exception:{e}\n")
            print(self.url)
            raise e
        return self._pages_count
