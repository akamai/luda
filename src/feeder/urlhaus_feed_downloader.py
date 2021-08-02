from typing import List

from src.feeder.feed_downloader import Url
from src.feeder.feed_downloader import FeedDownloader


class URLHausFeedDownloader(FeedDownloader):
    def fetch(self) -> List[Url]:
        import requests
        urlhaus_url = "https://urlhaus.abuse.ch/downloads/text_recent/"
        malicious_urls = requests.get(urlhaus_url).content.decode('utf-8').split('\r\n')
        return [Url(url, 'URLHaus', 'malicious') for url in malicious_urls]
