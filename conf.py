"""
conf.py

We store here alsmot all internal global variables for this project. To configure your project, in general
you'll need to use config.json
"""

import os

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

SRC_DIR = os.path.join(WORKING_DIR, 'src')

LUDA_OUTPUT = os.path.join(WORKING_DIR, 'luda_output')

CONFIG_FILE = os.path.join(WORKING_DIR, 'config.json')

# Data

DATA = os.path.join(WORKING_DIR, 'data')

PREPROCESSED_SUFFIX = '_preprocessed.csv'

DATA_LABELS = ['malicious', 'benign']

VT_KEY = os.path.join(WORKING_DIR, 'vt_key.txt')

# Clustering

MATRIX_FOLDER = os.path.join(LUDA_OUTPUT, 'matrix_output')

MATRIX_STATS_FOLDER = os.path.join(LUDA_OUTPUT, 'matrix_stats')

DISTANCE_MATRIX = 'matrix.pkl'

INDEX = 'index.pkl'

MATRIX_STATS = 'matrix_stats.pkl'

SIMILARITY_MAX = 100

INDEX_TO_KEEP = 'index_to_keep.pkl'

LABELS = 'labels.pkl'

# Logs

LOGGER_NAME = 'luda'

LOG_FOLDER = os.path.join(LUDA_OUTPUT, 'logs')

LOGGER_FILE = os.path.join(LOG_FOLDER, 'luda.log')

LOG_FILE_SIZE = 10 * 1000000  # 10 MB

LOG_FILE_NUMBER = 5

# Regex

REGEX_FOLDER_OUTPUT = os.path.join(LUDA_OUTPUT, 'regex_output')

REGEX_FOLDER = os.path.join(SRC_DIR, 'regex')

REGEX_SH = os.path.join(REGEX_FOLDER, "ConsoleRegexTurtle", "dist", 'regexturtle.sh')

REGEX_JAVA = os.path.join(REGEX_FOLDER, "ConsoleRegexTurtle", "dist", 'ConsoleRegexTurtle.jar')

REGEX_TMP = os.path.join(REGEX_FOLDER_OUTPUT, 'tmp')

BENIGN_FOR_RETRAIN = 20

TEST_BATCH_SIZE = 50000

REGEX_RUNNER = os.path.join(REGEX_FOLDER, 'RegexRunner.jar')

INPUT_REGEX_RUNNER = os.path.join(REGEX_FOLDER_OUTPUT, 'input_regex_runner.json')

OUTPUT_REGEX_RUNNER = os.path.join(REGEX_FOLDER_OUTPUT, 'output_regex_runner.json')

LAST_REGEX_LIST = os.path.join(DATA, 'regex_list.json')

# Coverage

COVERAGE_FOLDER = os.path.join(LUDA_OUTPUT, 'coverage')

# Crawler

MAX_LEN_URL = 100

TIMEOUT_CRAWL = 10

DEPTH_MAX = 10
