import os
import pathlib

import conf
from src.feeder.feed_downloader import Url


def create_folder(path):
    """
    Create folder if it does not exist. If the function gets a file, it will create all the folders before
    :param path: path of a file or folders. Can also be a list
    :return: void
    """

    def delete_one_folder(_path):
        if "." in os.path.basename(_path):  # Check if it's a file
            _path = os.path.dirname(_path)
        pathlib.Path(_path).mkdir(parents=True, exist_ok=True)

    if isinstance(path, list):
        for _path in path:
            delete_one_folder(_path)
    elif isinstance(path, str):
        delete_one_folder(path)


def process_file_name(filename):
    """
    Process the main csv file. It contains the data before being preprocessed
    :param filename: path of the csv
    :return: filename fixed
    """
    assert filename.endswith(".csv")
    if not os.path.isabs(filename):
        create_folder(filename)
        filename = os.path.join(conf.DATA, os.path.basename(filename))
    return filename


def process_preprocessed_file_name(main_file, preprocess_file):
    default_preprocess_file = os.path.join(conf.DATA,
                                           f"{os.path.basename(main_file).replace('.csv', '')}"
                                           f"{conf.PREPROCESSED_SUFFIX}")
    if preprocess_file is None:
        return default_preprocess_file
    if not os.path.exists(preprocess_file):
        return default_preprocess_file

    return preprocess_file


def df_to_url_list(df):
    columns = list(Url.__annotations__)
    url_list = [Url(row[1][columns[0]], row[1][columns[1]], row[1][columns[2]], row[1][columns[3]]) for row in
                df.iterrows()]
    return url_list
