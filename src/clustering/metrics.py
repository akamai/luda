from collections import defaultdict

import Levenshtein as lev
from src.clustering import swalign

STATS = defaultdict(int)


def get_sw_distance(match, mismatch, gap_penalty):
    scoring = swalign.NucleotideScoringMatrix(match, mismatch)
    sw = swalign.LocalAlignment(scoring, gap_penalty=gap_penalty)
    return sw.align


def longest_sub(str_a, str_b, th=10):
    """
    Return the longest common substring between two strings.
    It also saves the result into a dictionary to make statistics
    :param str_a: str
    :param str_b: str
    :param th: size of the common string from which we can store it into the stat dict
    :return: 0 or 1
    """
    global STATS
    m = len(str_a)
    n = len(str_b)
    counter = [[0] * (n + 1) for x in range(m + 1)]
    longest = 0
    lcs_set = set()
    for i in range(m):
        for j in range(n):
            if str_a[i] == str_b[j]:
                c = counter[i][j] + 1
                counter[i + 1][j + 1] = c
                if c > longest:
                    lcs_set = set()
                    longest = c
                    lcs_set.add(str_a[i - c + 1:i + 1])
                elif c == longest:
                    lcs_set.add(str_a[i - c + 1:i + 1])
    if len(lcs_set) >= 1:
        if len(list(lcs_set)[0]) >= th:
            STATS[list(lcs_set)[0]] += 1
            return 1
    return 0


DISTANCE_FUNC = {'sw': get_sw_distance(match=1, mismatch=-1, gap_penalty=-1),
                 'lev': lev.distance,
                 'longest': longest_sub}
