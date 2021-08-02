import os
import pandas as pd
import logging

from src.utils import create_folder
from src.utils import df_to_url_list
from src.feeder.feed_downloader import FeedDownloader, Url
import conf

logger = logging.getLogger(conf.LOGGER_NAME)


class UseCaseFeeder(object):

    @staticmethod
    def fetch(sources):
        """
        Once you create your feeder, add it here to call it directly from config.json
        :param sources: source list
        :return: url list object
        """
        url_list = []
        for source in sources:
            if source == 'urlhaus':
                from src.feeder.urlhaus_feed_downloader import URLHausFeedDownloader
                feeder_object = URLHausFeedDownloader()
            elif source == 'openfish':
                from src.feeder.openfish_feed_downloader import OpenPhishFeedDownloader
                feeder_object = OpenPhishFeedDownloader()
            elif source == 'alexa':
                from src.feeder.alexa_feed_downloader import AlexaFeedDownloader
                feeder_object = AlexaFeedDownloader()
            elif source == 'majestic':
                from src.feeder.vt_feed_downloader import VtFeedDownloader
                feeder_object = VtFeedDownloader()
            elif source == 'umbrella':
                from src.feeder.umbrella_feed_downloader import UmbrellaFeedDownloader
                feeder_object = UmbrellaFeedDownloader()
            elif source == 'iscx':
                from src.feeder.iscx_feed_downloader import IscxFeedDownloader
                feeder_object = IscxFeedDownloader()
            elif source == 'vt':
                from src.feeder.vt_feed_downloader import VtFeedDownloader
                feeder_object = VtFeedDownloader()
            else:
                continue
            url_list += feeder_object.run()

        return url_list

    @staticmethod
    def fetch_and_save(sources, filename):
        list_of_urls = UseCaseFeeder.fetch(sources)
        if os.path.exists(filename):
            logger.info(f'Found an existing {filename}. We append the feeders results to this file.')
            df = pd.read_csv(filename)
            assert list(df) == list(Url.__annotations__)
            list_of_urls += df_to_url_list(df)
        create_folder(filename)
        FeedDownloader.save_to_csv(list_of_urls, filename)
