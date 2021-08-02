import logging
import logging.handlers
import sys
import os
import pathlib
import conf


def init_logger(debug_mode=True, logger_file=conf.LOGGER_FILE):
    """
    Init logger file and print the log in stdout in debug_mode
    :param debug_mode: bool
    :param logger_file: path of the file log
    :return: logger object
    """
    if not os.path.exists(conf.LOG_FOLDER): # we don't use the function from utils to not create a circular dependency
        pathlib.Path(conf.LOG_FOLDER).mkdir(parents=True, exist_ok=True)
    _logger = logging.getLogger(conf.LOGGER_NAME)
    _logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    fh = logging.handlers.RotatingFileHandler(
        logger_file, maxBytes=conf.LOG_FILE_SIZE, backupCount=conf.LOG_FILE_NUMBER)

    fh.setFormatter(formatter)
    _logger.addHandler(fh)

    if debug_mode:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        _logger.addHandler(stdout_handler)

    return _logger
