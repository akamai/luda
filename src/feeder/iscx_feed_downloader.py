import requests
from io import BytesIO
from zipfile import ZipFile

from src.feeder.feed_downloader import FeedDownloader
from src.feeder.feed_downloader import Url
from src.feeder.crawler.crawler import Crawler


class IscxFeedDownloader(FeedDownloader):
    DOWNLOAD_URL = "http://205.174.165.80/CICDataset/ISCX-URL-2016/Dataset/ISCXURL2016.zip"

    def fetch(self):
        resp = requests.get(self.DOWNLOAD_URL, headers=Crawler.HEADERS).content
        zipfile = ZipFile(BytesIO(resp))
        result = []
        for line in zipfile.open("FinalDataset/URL/Benign_list_big_final.csv").readlines():
            result.append(Url(line.decode('utf-8').replace('/\r\n', ""), 'iscx', 'benign'))
        return result
