from typing import List
from src.logger_code import init_logger
import pytest
import mock

from src.feeder.feed_downloader import FeedDownloader
from src.feeder.feed_downloader import Url


@pytest.fixture
def feed_downloader_generic():
    class ExampleFeedDownloader(FeedDownloader):
        def fetch(self) -> List[Url]:
            source = 'Example source'
            phishingURL = Url("http://example.com/index.html", source, 'malicious')
            malwareURL = Url("http://example.com/index2.html", source, 'malicious')
            return [phishingURL, malwareURL]

    example_downloader = ExampleFeedDownloader()
    init_logger()
    return example_downloader


def test_fetch(feed_downloader_generic):
    example_urls = feed_downloader_generic.fetch()
    assert example_urls[0].source == 'Example source'
    assert {url.label for url in example_urls} == {'malicious'}


@pytest.mark.skip(reason="functional test. Comment this line to run the function")
def test_save_to_csv(feed_downloader_generic):
    list_of_urls = feed_downloader_generic.fetch()
    feed_downloader_generic.save_to_csv(list_of_urls)


@mock.patch('src.feeder.feed_downloader.Crawler')
def test_get_urls_from_domain(crawler_mock, feed_downloader_generic):
    url = 'akamai.com'
    depth = 30
    feed_downloader_generic.get_urls_from_domain(url, depth_max=depth)
    crawler_mock.assert_called_with(url, depth=depth)
