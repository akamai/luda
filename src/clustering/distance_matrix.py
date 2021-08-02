import numpy as np
import shutil
import pickle
import time
import os
import logging
import multiprocessing as mp
from collections import defaultdict
from tqdm import tqdm

from src.utils import create_folder
from src.clustering.metrics import DISTANCE_FUNC
import conf

logger = logging.getLogger(conf.LOGGER_NAME)


class DistanceMatrix(object):
    def __init__(self, url_list, matrix=None, distance_func=None, folder=None):
        """
        Compute distance matrix from list of strings
        :param url_list: list of urls or paths
        :param matrix: ndarray
        :param distance_func: Example distance_func=lev.distance or DISTANCE_FUNC['sw']
        :param folder: folder to save the results
        """
        self.distance_func = distance_func
        if not distance_func:
            self.distance_func = DISTANCE_FUNC['sw']
        self.url_list = url_list
        self.matrix = matrix
        self.folder = folder
        self.stats = defaultdict(int)

    def run(self, ncores=mp.cpu_count(), skip_calc=False):
        """
        Compute the matrix distances with multiprocessing
        :param ncores: number of cores to use
        :param skip_calc: bool. If True, skip the computation to the loading phase only
        :return:
        """
        if not skip_calc:
            create_folder(conf.MATRIX_FOLDER)
            self.__delete_matrix_stat_folder()
            _input_distance = self.__get_argument_create_matrix(ncores)
            processes = [mp.Process(target=self.__create_matrix_distance, args=x) for x in _input_distance]

            for p in processes:
                p.start()
            for p in processes:
                p.join()

        matrix = self.__get_big_matrix()  # to allocate as much as you want of memory in the kernel echo 1 > /proc/sys/vm/overcommit_memory
        self.matrix = matrix
        self.stats = self.__get_big_stats()

        self.__save()
        self.__delete_matrix_stat_folder(delete_folder=True)

        return matrix

    @classmethod
    def load(cls, folder_save):
        """
        Load a save folder for a future use, clustering for example.
        :param folder_save: path of the save folder
        :return: void
        """
        with open(os.path.join(folder_save, conf.DISTANCE_MATRIX), 'rb') as pickle_file:
            distance_matrix = pickle.load(pickle_file)
        with open(os.path.join(folder_save, conf.INDEX), 'rb') as pickle_file:
            index = pickle.load(pickle_file)
        return cls(index, distance_matrix, folder=folder_save)

    def __get_argument_create_matrix(self, ncores):
        """
        This function will map the computation and will give the arguments to be passed to the function
        create_matrix_distance
        :param ncores: number of cores to use
        :return: list of tuple
        """
        nsamples = len(self.url_list)

        distance_number = nsamples * (nsamples + 1) / 2  # we compute only half of the matrix
        computation_per_core = round(distance_number / ncores)
        computation_tuple_list = []
        a = nsamples
        b = nsamples  # in case ncores = 1
        for i in range(ncores - 1):
            b = self.__get_a(a, computation_per_core)
            computation_tuple_list.append((a, b))
            a = b
        computation_tuple_list.append((b, 0))

        return computation_tuple_list

    def __create_matrix_distance(self, b, a):
        """
        Fill the matrix between line a and b.
        It dumps then only the lines filled ( to save space).
        :param b: int
        :param a: int
        :return: void
        """
        logger.info('Running Process {}'.format(os.getpid()))
        before = time.time()
        n = len(self.url_list)
        distance_matrix = np.zeros(shape=(b - a, n),
                                   dtype=np.int32)  # we need double for HDBScan. We create a rectangle to save memory
        for i in tqdm(range(b - a)):
            for j in range(a + i):
                try:
                    distance_score = self.distance_func(self.url_list[a + i], self.url_list[j])
                    distance_matrix[i, j] = int(round(100 * distance_score / max(len(self.url_list[a + i]), len(
                        self.url_list[j]))))  # we want a unique scale for short and
                    # long string. Scale 0: 100
                except Exception as e:
                    logger.error(
                        "Error {} when computing the distance between line {} and column {}".format(e, a + i, j))
        with open(os.path.join(conf.MATRIX_FOLDER, "{}_distance_matrix.pkl".format(a)), 'wb') as f:

            pickle.dump(distance_matrix, f, protocol=4)  # protocol=4 to dump matrices bigger than 4GB

        logger.info('Process {} done in {} s'.format(os.getpid(), time.time() - before))
        if self.stats:
            logger.info('Dumping stats')
            create_folder(conf.MATRIX_STATS_FOLDER)
            with open(os.path.join(conf.MATRIX_STATS_FOLDER, '{}_stats.pkl'.format(a)), 'wb') as f:
                pickle.dump(dict(self.stats), f)
        return distance_matrix

    def __save(self):
        """
        Save the final results into a folder. This folder can be then used for a clustering for example
        :return: void
        """
        if not self.folder:
            _time = int(time.time() * 1000)
            folder = 'save_{}'.format(_time)
            logger.info(f'No folder specified, we save the results in {folder}')
            os.mkdir(folder)
            self.folder = folder
        elif not os.path.isdir(self.folder):
            os.mkdir(self.folder)
        logger.info('Dumping matrix')
        with open(os.path.join(self.folder, conf.DISTANCE_MATRIX), 'wb') as f:
            pickle.dump(self.matrix, f, protocol=4)
        logger.info('Dumping index')
        with open(os.path.join(self.folder, conf.INDEX), 'wb') as f:
            pickle.dump(self.url_list, f)
        if self.stats:
            logger.info('Dumping stats')
            with open(os.path.join(self.folder, conf.MATRIX_STATS), 'wb') as f:
                pickle.dump(dict(self.stats), f)

    @staticmethod
    def __get_a(b, s):
        """
        In a triangular matrix, the number of cells to compute between line a and line b is 
        (b-a +1)*(a + b) /2
        We solved the equation to be able to get a given b and s.

        The idea is that s should be the same for all the processes
        :param b: line b - int
        :param s: int
        :return: a - int
        """
        return int((-1 - np.sqrt(4 * (-2 * s + b ** 2 + b))) / (-2))

    @staticmethod
    def __symmetrize(a):
        """
        Return a symmetrized version of a
        """
        return a + a.T - np.diag(a.diagonal())

    def __get_big_matrix(self, complete_with_zero=False):
        """
        Load all the matrices dumped by the function create_matrix_distance and symmetrize them
        :return: ndarray
        """
        matrix_list = []
        for file in sorted(os.listdir(conf.MATRIX_FOLDER), key=lambda x: int(x.split('_')[0])):
            logger.info('Loading {}'.format(file))
            with open(os.path.join(conf.MATRIX_FOLDER, file), 'rb') as f:
                matrix_list.append(pickle.load(f))
        concatenated_matrix = np.concatenate(matrix_list)
        if complete_with_zero:  # useful when we add new urls on a computed matrix
            concatenated_matrix = np.concatenate(
                (np.zeros(
                    shape=(concatenated_matrix.shape[1] - concatenated_matrix.shape[0], concatenated_matrix.shape[1]),
                    dtype=np.int32), concatenated_matrix),
                axis=0)
        full_matrix = self.__symmetrize(concatenated_matrix)
        np.fill_diagonal(full_matrix, conf.SIMILARITY_MAX)
        return full_matrix

    @staticmethod
    def __get_big_stats():
        """
        Load all the stats dumped by the processes and combine them
        :return: dict
        """
        stats = {}
        for file in sorted(os.listdir(conf.MATRIX_STATS_FOLDER)):
            logger.info('Loading {}'.format(file))
            with open(os.path.join(conf.MATRIX_STATS_FOLDER, file), 'rb') as f:
                stats.update(pickle.load(f))
        return stats

    @staticmethod
    def __delete_matrix_stat_folder(delete_folder=False):
        """
        Delete all the temp matrices dumped
        :param delete_folder: bool. If True delete the folder
        :return: void
        """
        for folder in [conf.MATRIX_FOLDER, conf.MATRIX_STATS_FOLDER]:
            shutil.rmtree(folder, ignore_errors=True)
        if not delete_folder:  # We clean the old matrix
            create_folder([conf.MATRIX_FOLDER, conf.MATRIX_STATS_FOLDER])
        logger.info('Old matrices deleted.')

    def add_url_list(self, url_list_to_add):
        """
        Add more samples to a precomputed matrices. Done in single process only.
        :param url_list_to_add:  url list to add
        :return: void
        """
        n = len(self.url_list)
        base_matrix = self.matrix
        self.url_list += url_list_to_add
        self.__delete_matrix_stat_folder()
        self.__create_matrix_distance(len(self.url_list), n)
        self.matrix = sum([self.__reshape_base_matrix(base_matrix, len(url_list_to_add)),
                           self.__get_big_matrix(complete_with_zero=True)])
        self.__save()

    @staticmethod
    def __reshape_base_matrix(base_matrix, n_to_add):
        """
        Use to add new urls to a precomputed distance matrix. It creates cells filled with 0 to the new value to be
        computed
        :param base_matrix: matrix distance computed
        :param n_to_add: number of samples to add
        :return: new matrix with the new shape
        """
        result = np.concatenate((base_matrix, np.zeros(shape=(n_to_add, base_matrix.shape[0]), dtype=np.int32)),
                                axis=0)
        result = np.concatenate((result, np.zeros(shape=(result.shape[0], n_to_add), dtype=np.int32)), axis=1)
        return result
