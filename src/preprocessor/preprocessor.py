import pandas as pd
import logging
import os
from random import randint
from abc import ABC, abstractmethod
from tqdm import tqdm
from urllib.parse import urlparse

from src.utils import create_folder
import conf

logger = logging.getLogger(conf.LOGGER_NAME)


class Preprocessor(ABC):
    """
    Abstract class for preprocessing classes
    """

    def run(self, file_path):
        """
        Basic runner
        :param file_path: path of the main file. In general data.csv
        :return: void
        """
        df = pd.read_csv(file_path)
        df_basic_processed = self.basic_preprocessing(df)

        df_processed = self.process(df_basic_processed)
        create_folder(path=conf.DATA)
        preprocessed_file_name = os.path.join(conf.DATA,
                                              os.path.basename(file_path).replace('.csv', conf.PREPROCESSED_SUFFIX))
        logger.info(f"Data preprocessed saved in  {preprocessed_file_name}")
        df_processed.to_csv(preprocessed_file_name, index=False)
        return df_processed

    @abstractmethod
    def process(self, df):
        """
        Abstract method that needs to be implemented.
        :param df: DataFrame object.
        :return: DataFrame object after your filter
        """
        raise NotImplementedError

    @staticmethod
    def basic_preprocessing(df):
        """
        This technique run before your preprocessing and extracts for you some basic features
        :param df: DataFrame with benign and malicious samples
        :return: DataFrame object with the new columns
        """
        features_dict_list = []
        df = df.dropna(subset=['url'])
        urls = df['url'].unique()
        logger.info(f"{len(urls)} unique URLs found in the dataframe (shape {df.shape})")
        for url in tqdm(urls):
            full_url = url
            if full_url.startswith("/"):  # it's maybe only a path
                full_url = f"http://randomdomain{str(randint(0, 10 ** 5))}.com{full_url}"
            if not (full_url.startswith('http://') or full_url.startswith(
                    'https://')):  # URL parse is not working well without it
                full_url = 'http://{}'.format(full_url)
            full_url = full_url.replace('\n', '')
            parsed_uri = urlparse(full_url)
            extension = ''

            if parsed_uri.path.find('.') != -1 and not parsed_uri.path.endswith('/'):
                extension = parsed_uri.path[parsed_uri.path.rfind('.'):]
            features_dict_list.append(
                {"url": url,
                 'full_url': full_url,
                 'domain': parsed_uri.netloc,
                 'path': parsed_uri.path,
                 'params': parsed_uri.params,
                 'query': parsed_uri.query,
                 'path_len': len(parsed_uri.path),
                 'extension': extension,
                 'folder_count': parsed_uri.path.count('/')})

        result = pd.DataFrame(features_dict_list)
        result = pd.merge(df, result, how='left', on='url')
        result['url'] = result['full_url']
        result = result.drop(columns=['full_url'])
        logger.info('Final df shape {}'.format(result.shape))
        logger.info('Unique path: {}'.format(result['path'].nunique()))
        logger.info('Unique domain: {}'.format(result['domain'].nunique()))
        logger.info('Path with at least one folder: {} \n'.format(result[result['folder_count'] > 1]['path'].nunique()))
        return result
