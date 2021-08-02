import os
import pickle
import pandas as pd

import conf

import logging

logger = logging.getLogger(conf.LOGGER_NAME)


class UseCaseRegexGeneration(object):
    def __init__(self, regex_object):
        self.regex_object = regex_object

    def run(self, main_file, features_folder, cluster_list, benign_for_retrain=20,
            take_existing_result=False, round_max=15, min_path_for_run=1):
        """
        Take the data from the clustering step and extract the clusters
        :param main_file: file containing all the data.
        :param features_folder: folder_path with the features.
        :param cluster_list: list of cluster number to process
        :param benign_for_retrain: int. Number of str to not match to take into account at each round
        :param take_existing_result: bool. if True, will start from the last result. It allows us to run several rounds
        not continuously
        :param round_max: int. Number of round max before abandoning the cluster because of the FP
        :param min_path_for_run: int. minimal number of paths to run the regex extraction process
        :return: void
        """

        df, df_benign = self.load_df(main_file, features_folder)
        str_to_not_match = df_benign['path'].unique()
        if len(df) < min_path_for_run:
            logger.error(
                'Not enough path to start the clustering. Paths: {} , Min paths : {}'.format(len(df), min_path_for_run))
            return
        cluster_dict = {}
        if len(cluster_list) == 0:
            cluster_list = df['cluster'].unique()
            logger.info('No cluster number given. Creating regex for all cluster.')
        for cluster in cluster_list:
            if cluster == -1:
                continue
            cluster_urls = list(df[df['cluster'] == cluster]['path'].unique())
            cluster_dict['cluster_' + str(len(cluster_urls)) + '_' + str(cluster)] = {'match': cluster_urls,
                                                                                      'unmatch': []}
        self.regex_object.run_with_benign_check(_cluster_dict=cluster_dict, benign_list=str_to_not_match,
                                                benign_for_retrain=benign_for_retrain,
                                                take_existing_result=take_existing_result, round_max=round_max)

    @staticmethod
    def load_df(main_file, features_folder):
        """
        Load the df with the labels and the cleaning done in the clustering phase.
        :param main_file: main csv file.
        :param features_folder: folder_path with the features.
        :return: DataFrame
        """
        df = pd.read_csv(main_file).drop_duplicates(['path'])  # we ensure that everything is unique
        df_benign = df[df['label'] == 'benign']
        df = df[df['label'] == 'malicious']
        with open(os.path.join(features_folder, conf.INDEX_TO_KEEP), 'rb') as f:
            index_to_keep = pickle.load(f)
        with open(os.path.join(features_folder, conf.LABELS), 'rb') as f:
            labels = pickle.load(f)
        df = df.iloc[index_to_keep, :]
        df['cluster'] = labels
        return df, df_benign
