import csv
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from src.feeder.crawler.crawler import Crawler
import conf

logger = logging.getLogger(conf.LOGGER_NAME)


@dataclass
class Url:
    """
    Basic format of URL
    """
    url: str
    source: str
    label: str
    family: str = None

    def __iter__(self):
        """
        We use this function for iterating over a list of URL object
        :return: iterator
        """
        return iter([self.url, self.source, self.label, self.family])

    def __post_init__(self):
        """
        Function that run after the init and convert to lowercase the label
        :return:
        """
        self.label = self.label.lower()
        assert self.label in ['benign', 'malicious']


class FeedDownloader(ABC):
    """
    Abstract feeder class.

    You need to implement the fetch method.
    """

    def run(self):
        """
        Runner
        :return: list of Url object
        """
        list_of_urls = self.fetch()
        source = list_of_urls[0].source
        logger.info(f'{len(list_of_urls)} downloaded from {source}')
        return list_of_urls

    @abstractmethod
    def fetch(self) -> List[Url]:
        """
        Need to be implemented by each subclass
        :return: list of Urls object
        """
        raise NotImplementedError

    def fetch_and_save(self, filename="data.csv"):
        """
        Fetch and save Urls to CSV
        :param filename: path of the csv
        :return: list of Urls object
        """
        list_of_urls = self.fetch()
        self.save_to_csv(list_of_urls, filename)
        return list_of_urls

    @staticmethod
    def save_to_csv(url_list, filename) -> None:
        """
        Save list of Urls to csv
        :param url_list: list of Url object
        :param filename: path where the csv wil be stored
        :return: void
        """
        columns = list(Url.__annotations__)
        with open(filename, 'w') as csv_file:
            wr = csv.writer(csv_file, delimiter=',')
            wr.writerow(columns)
            for url in url_list:
                wr.writerow(list(url))
        logger.info(f'{len(url_list)} URls written into {filename}')

    @staticmethod
    def get_urls_from_domain(_url, depth_max=5):
        """
        Convert domain to URLs. Run the crawler that will recursively look for URls from the same domain
        :param _url: url string
        :param depth_max: Max depth for crawling
        :return: url set ( not Url object)
        """
        crawler_object = Crawler(_url, depth=depth_max)
        return crawler_object.run()

    def domains_to_urls(self, domain_list):
        """
        List of domain to send to get_urls_from_domain
        :param domain_list: list of domain
        :return: all urls from all the domains
        """
        url_list = []
        for domain in domain_list:
            try:
                url_list += list(self.get_urls_from_domain(domain))
            except Exception as e:
                logger.exception(e)
        return url_list
