import pandas as pd
import logging
from typing import List


from src.feeder.feed_downloader import FeedDownloader
from src.feeder.feed_downloader import Url
import conf

logger = logging.getLogger(conf.LOGGER_NAME)


class AlexaFeedDownloader(FeedDownloader):
    MAX_DOMAIN = 5

    def fetch(self) -> List[Url]:
        alexa_top_1m = pd.read_csv("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip", names=['rank', 'domain'])
        urls = self.domains_to_urls(alexa_top_1m['domain'].head(self.MAX_DOMAIN))
        return [Url(url, 'Alexa', 'Benign') for url in urls]
