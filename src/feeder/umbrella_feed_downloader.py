import pandas as pd
from typing import List

from src.feeder.feed_downloader import Url
from src.feeder.feed_downloader import FeedDownloader


class UmbrellaFeedDownloader(FeedDownloader):
    def fetch(self) -> List[Url]:
        umbrella_domains = pd.read_csv("http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip",
                                       names=['rank', 'domain'])
        urls = self.domains_to_urls(umbrella_domains['domain'])

        return [Url(url, 'Umbrella', 'Benign') for url in urls]
