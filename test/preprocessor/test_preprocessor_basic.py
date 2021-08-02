import os
import pytest
import mock

from src.preprocessor.preprocessor_basic import PreprocessorBasic

current_folder = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def preprocessor():
    return PreprocessorBasic()


@mock.patch('src.preprocessor.preprocessor_basic.create_folder')
@mock.patch('src.preprocessor.preprocessor_basic.pd.DataFrame.to_csv')
def test_run(create_folder, to_csv_mock, preprocessor):
    file_path = os.path.join(current_folder, 'data', 'data_preprocessing_test.csv')
    df_preprocessed =preprocessor.run(file_path)
    assert 'filter_wp' in list(df_preprocessed)
