import pytest
import os
from src.use_case.use_case_data import UseCaseData
from src.logger_code import init_logger

test_folder = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))

logger = init_logger()


@pytest.fixture()
def use_case():
    return UseCaseData()


@pytest.mark.skip(reason="functional test. Can take time. Comment this line to run the function")
def test_run(use_case):
    main_file = os.path.join(test_folder, 'data', 'data.csv')
    additional_files = [os.path.join(test_folder, 'data', 'benign_alexa.hql.out'),
                        os.path.join(test_folder, 'data', 'iscx_benign.csv')]
    use_case.run(main_file, additional_files)
