import pandas as pd
from typing import List

from src.feeder.feed_downloader import FeedDownloader
from src.feeder.feed_downloader import Url


class MajesticFeedDownloader(FeedDownloader):
    MAX_MAJESTIC = 100

    def fetch(self) -> List[Url]:
        majestic_top_1m = pd.read_csv("http://downloads.majesticseo.com/majestic_million.csv", usecols=['Domain'])
        urls = self.domains_to_urls(majestic_top_1m['domain'].head(self.MAX_MAJESTIC))

        return [Url(url, 'Majestic', 'Benign') for url in urls]
