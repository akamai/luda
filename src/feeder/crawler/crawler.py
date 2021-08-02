import requests
import logging
import urllib.request
import urllib3
import ssl
import tldextract
from bs4 import BeautifulSoup

from .endrecursive import EndRecursive
import conf

logger = logging.getLogger(conf.LOGGER_NAME)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context


class Crawler(object):
    """
    This class contains all the methods related to url crawling
    """
    HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8",
               "Accept-Encoding": "gzip, deflate", "Accept-Language": "*", "Connection": "keep-alive",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/86.0.42400.198 Safari/537.36"}

    URLS = 'urls'
    opener = urllib.request.build_opener()
    opener.addheaders = [(v, k) for k, v in HEADERS.items()]
    urllib.request.install_opener(opener)

    def __init__(self, _url, lock=None, depth=conf.DEPTH_MAX):
        self.lock = lock
        self.main_domain = self.__get_primary_domain(_url)
        self.main_page = 'http://' + self.main_domain
        self.url = _url
        self.url_set = set()
        self.domain_redirected = self.main_domain  # By default it's the same value
        self.depth = depth

    def run(self):
        """
        Main method to run the crawler
        :return:
        """
        url_fixed = self.fix_url(self.url)
        try:
            self.recursive_crawl(url_fixed)
        except EndRecursive:
            return self.url_set

    def recursive_crawl(self, _url):
        """
        Recursive crawling on a website. It crawls all the urls found.
        :param _url: url to crawl
        :return: void
        """
        if not _url:
            return None
        self.end_recursive_check()
        request = self.__request(_url)
        if not request:  # request = None
            return
        if len(request.content) < 5:
            logger.info(f'We skip {_url}. EMPTY CONTENT')
            return
        soup = BeautifulSoup(request.content, 'html.parser')
        if len(self.url_set) == 0:  # The first one, we always process
            self.__check_for_redirection(request)
            self.url_set.add(_url)
            self.end_recursive_check()
        self.__parse(_url, soup)

    def __parse(self, _url, soup):
        """
        Parse the soup of the URL
        :param _url: url
        :param soup: bs4 object
        :return: void
        """
        for i in soup.find_all("a"):
            if 'href' not in i.attrs:
                continue

            href = i.attrs['href']
            if len(href) > conf.MAX_LEN_URL:
                logger.info('TOO LONG URL {}'.format(_url))
                continue

            if href.startswith("/"):
                href = self.main_page + href

            if href.startswith("http"):
                if not (self.__get_primary_domain(href).endswith(self.main_domain)) and (
                        not self.__get_primary_domain(href).endswith(self.domain_redirected)):
                    logger.debug('We skip {}'.format(href))
                    continue

                if href not in self.url_set:
                    self.url_set.add(href)
                    logger.info('Scraping {}'.format(href))
                    self.recursive_crawl(href)

    def __request(self, _url):
        """
        Make the requests and handles different exceptions
        :param _url: url
        :return: request object
        """
        try:
            request = requests.get(_url, timeout=conf.TIMEOUT_CRAWL, headers=self.HEADERS,
                                   verify=False)  # 10 seconds timeout
        except requests.exceptions.ConnectTimeout as e:
            logger.error("CONNECT TIMEOUT for {}".format(_url))
            return
        except requests.exceptions.ReadTimeout as e:
            logger.error("READ TIMEOUT for {}".format(_url))
            return
        except requests.exceptions.SSLError as e:
            logger.error("SSL Error for {}. Exception {}".format(_url, e))
            return
        except requests.exceptions.ConnectionError as e:
            try:
                if 'nodename nor servname provided, or not known' in e.args[0].reason.args[0]:
                    logger.error(f'{_url} DOWN')
                else:
                    logger.error(f'Connection error for requesting {_url}')
                return
            except Exception:
                logger.error(f'Connection error for requesting {_url}')
                return
        except Exception as e:
            logger.error(f'NEW error {e} for requesting {_url}')
            return
        return request

    def __check_for_redirection(self, request):
        new_url = request.url
        domain = self.__get_primary_domain(new_url)
        if domain != self.main_domain:
            self.domain_redirected = domain

    def __get_primary_domain(self, _url):
        """
        Get primary domain from an URL
        :param _url: url
        :return: primary domain
        """
        if self.lock:
            self.lock.acquire()
        primary_domain = tldextract.extract(_url).domain + '.' + tldextract.extract(_url).suffix
        if self.lock:
            self.lock.release()
        return primary_domain

    def end_recursive_check(self):
        if len(self.url_set) >= self.depth:
            logger.info('Depth max {} reached'.format(self.depth))
            raise EndRecursive()  # Nice way to cut the process

    @staticmethod
    def fix_url(domain):
        if "." not in domain:
            return None
        domain = domain.replace('\n', '')
        if domain.endswith('.'):
            domain = domain[:-1]
        if not domain.startswith("http"):
            domain = f'http://{domain}'
        if domain.endswith('/'):
            domain = domain[:-1]
        return domain
