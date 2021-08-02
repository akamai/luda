import pytest
from src.feeder.crawler.crawler import Crawler


@pytest.fixture()
def crawler_object():
    return Crawler(_url='akamai.com', depth=2)


def test_fix_url():
    result = Crawler.fix_url('randomurl.com/')
    assert result == 'http://randomurl.com'


def test_run(crawler_object):
    url_set = crawler_object.run()
    print(url_set)
    assert len(url_set) >= 2 # depth
