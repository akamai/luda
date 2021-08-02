import pytest
import os
import json
import mock
from unittest.mock import patch

from src.logger_code import init_logger
from src.regex.regex import Regex
import conf

current_folder = os.path.dirname(os.path.abspath(__file__))

INPUT_CLUSTER = os.path.join(current_folder, 'data/input_cluster_2_1.json')
DATA = os.path.join(current_folder, 'data')


@pytest.fixture()
def regex_object():
    init_logger()
    return Regex(project_name='test_project')


@mock.patch('src.regex.regex.subprocess')
def test_run_regex_extraction(subprocess_mock, regex_object):
    regex_object.run_regex_extraction(json_to_extract={'randomjson'})
    assert subprocess_mock.run.called


@pytest.mark.skip(reason="regex functional test")
def test_run_regex_extraction_functional(regex_object):
    # Uncomment this test to really run the regex extraction. Took 2m 26sec on my computer 8cores 16Go RAM
    regex_object.run_regex_extraction(json_to_extract=INPUT_CLUSTER)


@mock.patch('src.regex.regex.json')
def test_create_json_cluster(json_mock, regex_object):
    str_list = ['/chase/home/auth/Logging_in.php',
                '/log/home/auth/Logging_in.php']
    str_to_not_match = ['wp-content/uploads',
                        'home.php']
    with open(INPUT_CLUSTER) as json_file:
        json_for_regex_extraction = json.load(json_file)
    with mock.patch('builtins.open') as open_mock:
        name = 'test_cluster'
        json_for_regex_extraction['name'] = name
        json_path = os.path.join(regex_object.project_folder, 'input_' + name + '.json')

        regex_object.create_json_cluster(str_list, str_to_not_match, name=name)
        assert json_mock.mock_calls[0][1][0] == json_for_regex_extraction
        open_mock.assert_called_with(json_path, 'w')


@pytest.mark.skip(reason="regex functional test")
def test_run_with_benign_check(regex_object):
    # Uncomment this test to really run the regex extraction. Took 2m 26sec on my computer 8cores 16Go RAM

    """
    Toook 6m 40 sec in my computer ( 8 cpu, 16go RAM)
    :param regex_object:
    :return:
    """
    cluster_dict = {'cluster_7_53': {'match': [
        '/wp-admin/jpmorgan/chasebank/chase/home/auth/Logon_Files/Themes/default/css/style.css',
        '/wp-admin/jpmorgan/chasebank/chase/home/auth/Logon_Files/Themes/guest/css/style.css',
        '/wp-admin/jpmorgan/chasebank/chase/home/auth/Logon_Files/Themes/default/css/style_new.css',
        '/wp-admin/jpmorgan/chasebank/chase/home/auth/Logon_Files/Themes/default-col/css/style_new.css',
        '/wp-admin/jpmorgan/chasebank/chase/home/auth/Logon_Files/Themes/guest/css/style_new.css',
        '/wp-admin/jpmorgan/chasebank/chase/home/auth/Logon_Files/Themes/default-col/css/style.css',
        '/wp-admin/jpmorgan/chasebank/chase/home/auth/logon_files/themes/default-col/css/style.css'],
        'unmatch': []},
        'cluster_11_3': {
            'match': ['/ch18', '/ch16', '/ch13', '/ch10', '/ch17', '/ch1', '/ch11', '/ch12', '/ch19',
                      '/ch14', '/ch15'], 'unmatch': []}}

    str_to_not_match = ['wp-content/uploads',
                        'home.php']
    regex_object.run_with_benign_check(cluster_dict, benign_list=str_to_not_match,
                                       benign_for_retrain=2, take_existing_result=False, round_max=2)


def test_check_regex_list(regex_object):
    regex_object = Regex(project_name='test')
    sig = ".s"
    string_list = ['luda', 'superman', 'akamai', 'blackhat', 'awordthatendswiths']
    expected = (1, ['awordthatendswiths'])
    match_result = regex_object.check_regex_list(sig, string_list, limit=10)
    assert expected == match_result


def test_get_cluster_results(regex_object):
    """
    To run this test. You should have the file test/regex/data/results_cluster_2_1.json
    :param regex_object:
    :return:
    """
    regex_object.project_folder = DATA
    cluster_results = regex_object.get_cluster_results()
    assert cluster_results == {'cluster_2_1': '/\\w++(\\w?+[^@])++'}


@mock.patch('src.regex.regex.pd.DataFrame.to_csv')
def test_create_result_report(to_csv_mock, regex_object):
    regex_object.project_folder = DATA
    df = regex_object.create_result_report()
    assert df['name'].to_list() == ['cluster_2_1']
    assert df['regex_java'].to_list() == ['/\\w++(\\w?+[^@])++']


def test_run_regex_java():
    regex = "(?:\w*+/)*+bt_version_checker\.php"
    string_list = ['/spyeye/Main/bt_version_checker.php', '/spye/main/bt_version_checker.php',
                   '/WP-CD/Main/bt_version_checker.php', '/Net/Main/bt_version_checker.php',
                   '/main/main/bt_version_checker.php', '/dbase/main/bt_version_checker.php',
                   '/hits/bt_version_checker.php', '/Main/bt_version_checker.php', '/spy/main/bt_version_checker.php',
                   '/sy1/bt_version_checker.php', '/grab/main/bt_version_checker.php']

    result = Regex.run_regex_java(regex, string_list)
    assert set(result) == {True}


@patch('conf.OUTPUT_REGEX_RUNNER', os.path.join(current_folder, 'data/output_regex_runner.json'))
@patch('conf.INPUT_REGEX_RUNNER', os.path.join(current_folder, 'data/input_correct.json'))
def test_run_regex_java_with_file():
    new_open = open(conf.OUTPUT_REGEX_RUNNER, 'r')
    # By doing that, I can patch only the first open call
    with mock.patch('builtins.open') as mymock:
        mymock.side_effect = [mock.MagicMock(), new_open]
        regex = "(\\.?+[^_])++"
        result = Regex.run_regex_java(regex, '')
        assert result == [True, True]
