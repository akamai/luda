import pandas as pd
import logging
import os

import conf
from src.feeder.feed_downloader import Url

logger = logging.getLogger(conf.LOGGER_NAME)


class UseCaseData(object):

    def run(self, main_file, additional_sources):
        final_df = pd.DataFrame(columns=list(Url.__annotations__))
        if os.path.exists(main_file):
            df = pd.read_csv(main_file)
            assert list(df) == list(Url.__annotations__)
            logger.info(
                f'{main_file} already exists. We load it and concatenate it with the additional sources ( if exists)')
            final_df = pd.concat([final_df, df])
        for path_label in additional_sources:
            final_df = pd.concat([final_df, self.get_basic_format_df(path_label['path'], path_label['label'])])
        final_df.to_csv(main_file, index=False)
        return final_df

    def get_basic_format_df(self, file, label):
        self.check_label(label=label)
        df = self.load_df(file)
        df['label'] = label.lower()
        new_df = pd.DataFrame(df['url'])
        other_columns = list(Url.__annotations__)
        other_columns.remove('url')
        for column in other_columns:
            if column in df.columns:
                new_df = pd.concat([new_df, df[column]], axis=1)
            else:
                logger.warning(f'Column {column} not found in {file}. Setting it to None')
                new_df[column] = None
        logger.info(f"{new_df['url'].nunique()} unique URLs loaded from {file}")
        return new_df

    @staticmethod
    def check_label(label):
        if label.lower() not in conf.DATA_LABELS:
            raise Exception('You should specify a label ( malicious or benign) for you data sources')

    def load_df(self, file_path):
        SEP = [',', '\t']  # you put here several sep if you have different formats
        for sep in SEP:
            try:
                df = pd.read_csv(file_path, sep=sep, error_bad_lines=False)
                try:
                    self.check_columns(df)
                except Exception:  # maybe with the next sep, it will work.
                    continue
                return df
            except Exception as e:
                raise Exception(f'Failed loading for file {file_path}, {e}')
        raise Exception(f'Failed loading for file {file_path}')

    @staticmethod
    def check_columns(df):
        MANDATORY_COLUMNS = ['url']
        for col in MANDATORY_COLUMNS:
            if col not in df.columns:
                raise Exception(f"You should have a column named {col} at least")
