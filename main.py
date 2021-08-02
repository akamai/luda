import json

from src.logger_code import init_logger
from src.regex.regex import Regex
from src.use_case.use_case_clustering import UseCaseClustering
from src.use_case.use_case_regex_generation import UseCaseRegexGeneration
from src.use_case.use_case_feeder import UseCaseFeeder
from src.use_case.use_case_preprocessor import UseCasePreprocessor
from src.use_case.use_case_data import UseCaseData
from src.utils import process_file_name
from src.utils import process_preprocessed_file_name
import conf

__author__ = "Jordan Garzon"
__email__ = "jgarzon@akamai.com"

with open(conf.CONFIG_FILE) as json_file:
    config = json.load(json_file)


def main():
    logger = init_logger()
    main_file = process_file_name(config['main_file'])
    preprocessed_file = process_preprocessed_file_name(main_file, config['clustering']['preprocessed_file'])
    if config['data']['run']:
        UseCaseData().run(main_file, config['data']['additional_files'])
    if config['feeder']['run']:
        logger.info('Running the feeders')
        UseCaseFeeder().fetch_and_save(config['feeder']['sources'], main_file)

    if config['preprocessing']['run']:
        logger.info('Running the preprocessing')
        UseCasePreprocessor().run(config['preprocessing']['name'], main_file)

    if config['clustering']['run']:
        logger.info('Running the clustering')

        use_case_clustering = UseCaseClustering()
        use_case_clustering.run(file_path=preprocessed_file,
                                skip_compute_distance=config['clustering']['skip_distance_computation'],
                                save_folder=config['clustering']['features_folder'],
                                clusterer=config['clustering']['clusterer'],
                                filter_th=config['clustering']['filter_similarity'])

    # Regex Step
    if config['regex']['run']:
        logger.info('Running the regexes')
        regex_object = Regex(project_name=config['regex']['regex_folder'])
        use_case_regex = UseCaseRegexGeneration(regex_object)

        use_case_regex.run(main_file=preprocessed_file,
                           cluster_list=config['regex']['cluster_list'],
                           features_folder=config['clustering']['features_folder'],
                           benign_for_retrain=config['regex']['benign_for_retrain'],
                           take_existing_result=config['regex']['take_existing_result'],
                           round_max=config['regex']['round_max'],
                           min_path_for_run=config['regex']['min_path_for_run'])


if __name__ == '__main__':
    main()
