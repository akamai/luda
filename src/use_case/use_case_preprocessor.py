import logging

import conf

logger = logging.getLogger(conf.LOGGER_NAME)


class UseCasePreprocessor(object):
    """
    Add here your preprocessing technique following the "basic" syntax one.
    """
    @staticmethod
    def run(preprocess_name, file_path):
        if preprocess_name == 'basic':
            from src.preprocessor.preprocessor_basic import PreprocessorBasic
            PreprocessorBasic().run(file_path)
