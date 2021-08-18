import logging
import os
import pickle
import pandas as pd
import json

from src.preprocessor.preprocessor import Preprocessor
from src.regex.regex import Regex
from src.utils import create_folder

import conf

logger = logging.getLogger(conf.LOGGER_NAME)

MIN_LEN = 7
MAX_PATH = 45000


class PreprocessorBasic(Preprocessor):
    """
    Basic preprocessor class. It filters duplicates, Urls already caught by the old regexes, too long path,
    select one path per domain etc
    """

    def process(self, df):
        """
        Method that had to be implemented. Run all the submethod and the return a DataFrame filtered.
        :param df: DataFrame
        :return: DataFrame filtered
        """
        df_benign = df[df['label'] == 'benign']
        df = df[df['label'] == 'malicious']
        number_of_path_before_cleaning = df['path'].nunique()
        df = self.remove_path_duplicates(df)
        df = self.keep_one_path_per_domain(df)
        df = self.clean_df(df, benign_path=df_benign['path'].unique())
        df = self.keep_path_with_folders(df)
        df = self.clean_with_regexes(df)
        df = self.check_size(df)
        self.show_stat(df)
        logger.info(
            'In total we cleaned {} (- {} %) paths'.format(number_of_path_before_cleaning - df['path'].nunique(),
                                                           (1 - df[
                                                               'path'].nunique() / number_of_path_before_cleaning) * 100))
        return pd.concat([df, df_benign], sort=False)

    @staticmethod
    def remove_path_duplicates(df):
        """
        It should be mandatory. Take unique paths
        :param df: DataFrame
        :return: DataFrame
        """
        logger.info('Shape with path duplicates : {}'.format(df.shape))
        result = df.drop_duplicates(['path'])
        logger.info('Shape without path duplicates : {} (-{} %)'.format(result.shape,
                                                                        round(100 - 100 * result.shape[0] / df.shape[0],
                                                                              2)))
        return result

    @staticmethod
    def keep_one_path_per_domain(df):
        """
        To reduce the number of paths and to more generalize the regexes, we can choose only one path per domain
        :param df: DataFrame
        :return: DataFrame
        """
        logger.info('Shape with domain duplicates : {}'.format(df.shape))
        result = df.drop_duplicates(['domain'])
        logger.info('Shape without domain duplicates : {} (-{} %)'.format(result.shape,
                                                                          round(
                                                                              100 - 100 * result.shape[0] / df.shape[0],
                                                                              2)))
        return result

    @staticmethod
    def show_stat(df):
        """
        Show basic stats
        :param df: DataFrame
        :return: void
        """
        logger.info('Shape {}'.format(df.shape))
        logger.info('Path : {}'.format(df['path'].nunique()))
        logger.info('Domain : {}'.format(df['domain'].nunique()))
        logger.info('Mean path len: {}'.format(df['path_len'].mean()))

    def clean_df(self, df, benign_path, path_len=MIN_LEN):
        """
        Some basic cleaning
        :param df: DataFrame
        :param benign_path: list of benign path
        :param path_len: minimal path len
        :return: DataFrame
        """
        df['filter_wp'] = df['path'].apply(self.clean_wordpress, args=(MIN_LEN,))
        new_df = df[(df['path_len'] >= path_len) & (~df['path'].isin(benign_path)) & (df['filter_wp'] == False)]
        logger.info('Cleaning : {} -- > {} paths (-{}%)'.format(df['path'].nunique(), new_df['path'].nunique(),
                                                                round(new_df['path'].nunique() / df['path'].nunique(),
                                                                      2)))
        return new_df

    def clean_with_regexes(self, df):
        """
        Remove from the DataFrame Urls already caught by your existing regexes.
        :param df: DataFrame object
        :return: DataFrame filtered
        """
        if not os.path.exists(conf.LAST_REGEX_LIST):
            logger.info('We did not find {}. We skip the cleaning with regexes step'.format(conf.LAST_REGEX_LIST))
            return df
        with open(conf.LAST_REGEX_LIST) as json_file:
            regex_list = json.load(json_file)['regexes']
        already_found = self.regex_test(regex_list, list(df[df['path'].notnull()]['path'].unique()))[0]
        logger.info('{} paths are already found with the old regexes'.format(len(already_found)))
        df = df[~df['path'].isin(list(already_found))]
        return df

    @staticmethod
    def regex_test(regex_list, list_to_test, pickle_save=os.path.join(conf.COVERAGE_FOLDER, 'nevada_coverage.pickle')):
        """

        :param regex_list: regex list ( string )
        :param list_to_test: list of urls to test
        :param pickle_save: if specified, save the statistics of this test in a pickle that you can open with the
        Jupyter Notebook for analysis
        :return: tuple (set of Urls found, dictonnary with catches by regex, DataFrame with some stats)
        """
        all_found = set()
        dict_found = {}
        for _re in regex_list:
            print(f'Testing regex {_re}')
            _, found = Regex.check_regex_list(_re, list_to_test)
            print(f'Match {len(found)} paths !')
            dict_found[_re] = found
            all_found = all_found.union(set(found))
        data = {'regex': list(dict_found.keys()), 'count': [len(x) for x in list(dict_found.values())]}

        df_stat = pd.DataFrame(data)
        print(f"Coverage {str(df_stat['count'].sum())} {round(100 * df_stat['count'].sum() / len(list_to_test), 2)} % ")
        if pickle_save:
            create_folder(pickle_save)
            with open(pickle_save, 'wb') as handle:
                pickle.dump(dict_found, handle, protocol=pickle.HIGHEST_PROTOCOL)
                print(f'Results saved in {pickle_save}')
        return all_found, dict_found, df_stat

    @staticmethod
    def keep_path_with_folders(df, th=1):
        """
        To avoid FP, sometimes we want to catch 'long' URLs, we more than one folder inside the path
        :param df: DataFrame
        :param th: number of folders minimum
        :return: DataFrame filtered
        """
        logger.info('Shape : {}'.format(df.shape))
        result = df[df['folder_count'] > th]
        logger.info('Shape with at least {} folder(s) : {} (-{} %)'.format(th, result.shape,
                                                                           round(100 - 100 * result.shape[0] / df.shape[
                                                                               0],
                                                                                 2)))
        return result

    @staticmethod
    def clean_wordpress(x, path_len_min):
        """
        Wordpress paths create many FP, we filter here the most popular paths
        :param x: url
        :param path_len_min: path len min
        :return: bool
        """

        def return_if_path_len_ok(x, key):
            return len(x.replace(key, '')) < path_len_min

        wordpress_dict = {'wp-admin': ['wp-admin/images', 'wp-admin/css', 'wp-admin/js'],
                          'wp-includes': ['wp-includes/css', 'wp-includes/js', 'wp-includes/images'],
                          'wp-content': ['wp-content/plugins', 'wp-content/themes', 'wp-content/uploads',
                                         'wp-content/languages/themes', 'wp-content/mu-plugins'],
                          'images': ['images/logos.gif', 'images/logo.gif'],
                          'contact': ['contact-us'],
                          'config.bin': [],
                          'admin.php': [],
                          'login.php': [],
                          'index.php': [],
                          'gate.php': [],
                          '.jpg': [],
                          '.png': [],
                          '.php': []}
        for wp_key in wordpress_dict:
            if wp_key in x:
                for wp_key_path in wordpress_dict[wp_key]:
                    if wp_key_path in x:
                        return return_if_path_len_ok(x, wp_key_path)
                return return_if_path_len_ok(x, wp_key)
        return False

    @staticmethod
    def check_size(df):
        """
        To avoid issue with computation, we can specifiy a limit of URLs to keep.
        30k unique paths can use 300GB RAM ...
        :param df: DataFrame
        :return: DataFrame after filter
        """
        if df['path'].nunique() > MAX_PATH:
            logger.info('r/!\ NUMBER OF PATHS TOO HIGH {}. WE SAMPLE {} paths'.format(df['path'].nunique(), MAX_PATH))
            return df.sample(MAX_PATH)
        return df
