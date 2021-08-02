import pytest
from src.logger_code import init_logger
from src.feeder.alexa_feed_downloader import AlexaFeedDownloader


@pytest.fixture()
def alexa_feeder():
    feeder = AlexaFeedDownloader()
    init_logger()
    return feeder


@pytest.mark.skip(reason="functional test. Can take time. Comment this line to run the feeder")
def test_fetch(alexa_feeder):
    urls = alexa_feeder.fetch()
    print(urls)
