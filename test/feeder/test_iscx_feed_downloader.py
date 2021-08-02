import pytest
from src.logger_code import init_logger
from src.feeder.iscx_feed_downloader import IscxFeedDownloader


@pytest.fixture()
def iscx_feeder():
    feeder = IscxFeedDownloader()
    init_logger()
    return feeder

@pytest.mark.skip(reason="functional test. Can take time. Comment this line to run the feeder")
def test_fetch(iscx_feeder):
    urls = iscx_feeder.fetch()
    print(urls)
    a = 1
