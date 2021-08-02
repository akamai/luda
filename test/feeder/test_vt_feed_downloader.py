import pytest
from src.logger_code import init_logger
from src.feeder.vt_feed_downloader import VtFeedDownloader

import mock


@pytest.fixture()
def vt_feeder():
    feeder = VtFeedDownloader()
    init_logger()
    return feeder


@pytest.mark.skip(reason="functional test. Can take time. Comment this line to run the feeder")
def test_fetch(vt_feeder):
    urls = vt_feeder.fetch()
    print(urls)


@mock.patch('builtins.open', mock.mock_open(read_data='my_vt_key'))
def test_load_key(vt_feeder):
    key = vt_feeder.load_key('data/vt_key.txt')
    assert key == 'my_vt_key'


@pytest.mark.skip(reason="functional test. Can take time. Comment this line to run the feeder")
def test_get_records(vt_feeder):
    url_list = vt_feeder.get_records(number=10)
    print(url_list)
