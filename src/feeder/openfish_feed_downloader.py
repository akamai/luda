import requests
from typing import List

from src.feeder.feed_downloader import Url
from src.feeder.feed_downloader import FeedDownloader


class OpenPhishFeedDownloader(FeedDownloader):
    def fetch(self) -> List[Url]:
        openphish_url = "https://openphish.com/feed.txt"
        malicious_urls = requests.get(openphish_url).content.decode('utf-8').split('\n')
        return [Url(url, 'OpenPhish', 'Malicious', "Phishing") for url in malicious_urls]
