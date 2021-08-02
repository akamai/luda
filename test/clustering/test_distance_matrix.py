import numpy as np
import pytest
import mock
import shutil

from src.clustering.distance_matrix import DistanceMatrix
from src.clustering.metrics import DISTANCE_FUNC
import conf

word_list = ['verify',
             'palaver',
             'bathrobe',
             'traitorwise',
             'midwatch',
             'onymal',
             'aphlogistic',
             'trustingly',
             'saponifier',
             'moodle',
             'isuret',
             'oedogoniaceous',
             'unhoard',
             'receiptless',
             'unfibbing',
             'header',
             'Tasian',
             'deferral',
             'expansively',
             'hydramnion']


# downloaded with nltk.word.words()


class DistanceMatrixSimple(object):
    def __init__(self, distance_func=DISTANCE_FUNC['sw']):
        self.distance_func = distance_func

    def create_matrix_distance(self, url_list):
        n = len(url_list)
        distance_matrix = np.zeros(shape=(n, n), dtype=np.double)  # we need double for HDBScan
        for i in range(n):
            for j in range(i + 1, n):
                distance_matrix[i, j] = int(
                    round(100 * self.distance_func(url_list[i], url_list[j]) / max(len(url_list[i]), len(url_list[j]))))
        distance_matrix = self.symmetrize(distance_matrix)
        np.fill_diagonal(distance_matrix, conf.SIMILARITY_MAX)
        return distance_matrix

    @staticmethod
    def symmetrize(a):
        return a + a.T - np.diag(a.diagonal())


@pytest.fixture()
def distance_matrix_object():
    return DistanceMatrix(word_list, distance_func=DISTANCE_FUNC['sw'])


def test_run(distance_matrix_object):
    """
    Here we test that the distance matrix with multiprocessing does the same job
    as the simple class written above
    :return:
    """
    expected = DistanceMatrixSimple().create_matrix_distance(word_list)

    output = distance_matrix_object.run()
    shutil.rmtree(distance_matrix_object.folder, ignore_errors=True)

    assert np.array_equal(expected, output)


def test_load(distance_matrix_object):
    distance_matrix_object.folder = 'data/save_test'
    distance_matrix_object.run()

    distance_matrix = DistanceMatrix.load('data/save_test')
    # shutil.rmtree(distance_matrix_object.folder, ignore_errors=True)
    assert np.array_equal(distance_matrix.matrix, distance_matrix_object.matrix)
    assert np.array_equal(distance_matrix.url_list, distance_matrix_object.url_list)


def test_add_url_list():
    distance_matrix = DistanceMatrix.load('data/save_test')
    distance_matrix.__save = mock.Mock()
    old_matrix_shape = distance_matrix.matrix.shape
    distance_matrix.add_url_list(['jordan', 'jordan.html', 'akamai'])
    assert distance_matrix.url_list[-3:] == ['jordan', 'jordan.html', 'akamai']
    assert distance_matrix.matrix.shape == (old_matrix_shape[0] + 3, old_matrix_shape[0] + 3)


def test__get_argument_create_matrix():
    distance_object = DistanceMatrix(url_list=list(range(100)))
    print(dir(distance_object))
    result = distance_object._DistanceMatrix__get_argument_create_matrix(ncores=5)  # works to call private method
    assert [(100, 90), (90, 79), (79, 66), (66, 49), (49, 0)] == result


@mock.patch('builtins.open')
def test__create_matrix_distance(open_mock, distance_matrix_object):
    print('Len word list {}'.format(len(word_list)))
    a = 10
    b = 15
    word_list_processed = word_list[a:b]
    print(word_list_processed)
    result = distance_matrix_object._DistanceMatrix__create_matrix_distance(b, a)
    assert result.shape == (b - a, len(word_list))
    assert result[2, 3] == int(round(
        100 * distance_matrix_object.distance_func(word_list[a + 2], word_list[a + 3]) / max(len(word_list[a + 2]), len(
            word_list[a + 3]))))
