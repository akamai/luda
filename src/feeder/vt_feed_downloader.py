import requests
import math
import logging

from src.feeder.feed_downloader import FeedDownloader
from src.feeder.feed_downloader import Url
import conf

logger = logging.getLogger(conf.LOGGER_NAME)


class VtFeedDownloader(FeedDownloader):
    """
    This class can be used to bring either benign or malicious URLs.
    We use it currently to bring benign URLs. To force VT, to return URLs with a path, we add the path
    should include the letter "a". Don't forget to store your key in a file.
    """
    QUERY = """entity:url path:'a' response_code:200 p:0"""

    def __init__(self):
        self.bulk = 300  # Because the api does not accept a limit larger than 300
        self.api_key = self.load_key()
        self.headers = {'x-apikey': self.api_key}

    def fetch(self):
        return self.get_records()

    def get_records(self, query=QUERY, number=1000):
        if number <= self.bulk:
            bulk = number
        else:
            bulk = self.bulk

        params = {'query': query, 'limit': bulk}

        r = requests.get('https://www.virustotal.com/api/v3/intelligence/search', params, headers=self.headers)
        request_json = r.json()
        lst = request_json['data']
        number_of_bulks = math.ceil(((number - bulk) / bulk))
        for i in range(number_of_bulks):
            url = request_json['links']['next']
            r = requests.get(url, headers=self.headers)
            request_json = r.json()
            lst.extend(request_json['data'])

        return [Url(item['attributes']['last_final_url'], 'vt', 'benign') for item in lst]

    @staticmethod
    def load_key(_path=conf.VT_KEY):
        try:
            with open(_path) as f:
                key = f.read()
        except Exception as e:
            logger.error('You need store the VT API key in a file before continuing. You can put it in '
                         '{}'.format(conf.VT_KEY))
            return
        return key
