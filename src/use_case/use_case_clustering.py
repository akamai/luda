import pandas as pd
import pickle
import logging
import os
import numpy as np

from src.clustering.distance_matrix import DistanceMatrix
from src.clustering.metrics import DISTANCE_FUNC

import conf

logger = logging.getLogger(conf.LOGGER_NAME)

"""
###     Note about the following FP_LIST    ###

1. FP ( benign) path should be added on the data step OR filtered on the preprocessing step. If you
    don't want ( bad practice) to do it there you can add your benign path here.
2. The MAIN use case of this following list is to add benign path AFTER having run the distance matrix computation
    and saw some FP on your cluster. You can filter them here and run a new clustering.


"""


FP_LIST = ['/wp-content', '/index.php', '/wp-includes', '/gate.php', '/admin.php', '/wp-admin',
           '/wp-content/uploads',
           '/images/logo.gif', '/login.php']


# if you don't want to rerun the feeders. You can still filter some path here but we advise to it

def get_clusterer(clusterer_dict):
    """
    Return different clustering config. We advise to use DBscan.
    :param clusterer_dict: dict with clustering parameters. E.g {"dbscan": {"eps": 10, "min_samples": 8}}
    :return: clustering object
    """
    if not clusterer_dict:
        clusterer_dict = {"dbscan": {"eps": 10, "min_samples": 8}}
    if 'dbscan' in clusterer_dict:
        from sklearn.cluster import DBSCAN  # We import here so we don't need to install something we don't need
        return DBSCAN(**clusterer_dict['dbscan'], metric='precomputed')
    elif 'hdbscan' in clusterer_dict:
        import hdbscan
        return hdbscan.HDBSCAN(**clusterer_dict['dbscan'], metric='precomputed')
    elif 'complete' in clusterer_dict:
        from sklearn.cluster import AgglomerativeClustering
        return AgglomerativeClustering(**clusterer_dict['complete'], affinity='precomputed')


class UseCaseClustering(object):

    def run(self, file_path, skip_compute_distance=False, save_folder=None,
            clusterer=None, filter_th=10):
        """
        Compute the distance between URL and cluster them
        :param file_path: path of the csv preprocessed
        :param skip_compute_distance: bool. If true, does only the clustering
        :param save_folder: path. Mandatory if we skip the computation step
        :param clusterer: clustering technique
        :param filter_th: threshold used to clean the matrix in the function __filter_outlier_and_fp
        :return: void
        """
        if skip_compute_distance:
            assert save_folder is not None
            distance_matrix_object = DistanceMatrix.load(save_folder)
        else:
            df_features = pd.read_csv(file_path)
            df_features = df_features[df_features['label'] == 'malicious']
            logger.info(f"For this step, we do not use the "
                        f" {df_features[df_features['label'] == 'malicious']['path'].nunique()} benign paths ")
            df_features = df_features[~df_features['path'].isin(FP_LIST)]
            path_list = list(df_features['path'].unique())  # We take only unique !!!
            distance_matrix_object = DistanceMatrix(path_list,
                                                    distance_func=DISTANCE_FUNC['sw'], folder=save_folder)
            distance_matrix_object.run()
        distance_matrix_object.matrix = distance_matrix_object.matrix.astype(np.double)
        index_to_keep, matrix_filtered = self.__filter_outlier_and_fp(distance_matrix_object.matrix, filter_th,
                                                                      distance_matrix_object.url_list)
        distance_matrix_object.matrix = matrix_filtered
        logger.info('We begin the clustering !')
        distance_matrix_object.matrix = self.distance_from_sim(distance_matrix_object.matrix)
        clust = get_clusterer(clusterer)
        clust.fit(
            distance_matrix_object.matrix)  # we need to pass distance matrix instead of similarity
        logger.info('Clustering done')
        with open(os.path.join(distance_matrix_object.folder, 'labels.pkl'), 'wb') as f:
            pickle.dump(clust.labels_, f)
        with open(os.path.join(distance_matrix_object.folder, 'index_to_keep.pkl'), 'wb') as f:
            pickle.dump(index_to_keep, f)
        logger.info('You can find the results at {}'.format(distance_matrix_object.folder))

    @staticmethod
    def __filter_outlier_and_fp(mat, th, path_list=None):
        """
        Clean the matrix from outlier and FP
        :param mat: matrix
        :param th: int. If a row does not contain a value higher than th, it will be filtered.
        :param path_list: list
        :return: tuple. (list of indexes not filtered, the new matrix filtered)
        """
        index_to_remove = []
        if path_list:
            for fp in FP_LIST:
                if fp in path_list:
                    index_to_remove.append(path_list.index(fp))
        logger.info('Matrix size before filter {}'.format(mat.shape))
        new_matrix = []
        index_to_keep = []
        for i, el in enumerate(mat):
            if i in index_to_remove:
                continue
            if el.max() >= th:
                new_matrix.append(el)
                index_to_keep.append(i)

        new_matrix = np.vstack(new_matrix)
        new_matrix = new_matrix[:, index_to_keep]
        logger.info('Matrix size after filter {}'.format(new_matrix.shape))

        return index_to_keep, np.vstack(new_matrix)

    @staticmethod
    def distance_from_sim(matrix):
        """

        Invert linearly the numbers. Shift min --> max and max--> min. Ensure than the diagonal is 0
        The goal is to transform a similarity matrix into a distance matrix.
        :param matrix: matrix 2d
        :return: matrix 2d
        """
        high = conf.SIMILARITY_MAX
        result = np.abs(high - matrix)
        np.fill_diagonal(result, 0)  # we ensure that the edit distance with an element and itself is 0
        return result
