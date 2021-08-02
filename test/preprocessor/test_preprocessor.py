import os
import pytest
from src.preprocessor.preprocessor import Preprocessor

current_folder = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def preprocessor():
    return Preprocessor()


@pytest.mark.skip(reason="functional test. Can take time. Comment this line to run the function")
def test_run(preprocessor):
    file_path = os.path.join(current_folder, 'data.csv')
    preprocessor.run(file_path)
