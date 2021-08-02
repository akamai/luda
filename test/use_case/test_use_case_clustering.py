import pytest
import os

from src.use_case.use_case_clustering import UseCaseClustering
from src.logger_code import init_logger

test_folder = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def use_case():
    logger = init_logger()
    return UseCaseClustering()


@pytest.mark.skip(reason="functional test. Can take time. Comment this line to run the function")
def test_run(use_case):
    main_file = os.path.join(test_folder, 'data', 'data_preprocessed.csv')
    use_case.run(main_file)
