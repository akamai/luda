import json
import logging
import subprocess
import os
import shutil
import pandas as pd
from psutil import virtual_memory

import conf
from src.utils import create_folder

logger = logging.getLogger(conf.LOGGER_NAME)


class Regex(object):
    """
    This class handles the creation and test of Regex on a list of string.
    """

    def __init__(self, project_name, remove_project=False):
        self.project_name = project_name
        create_folder(conf.REGEX_FOLDER_OUTPUT)
        self.project_folder = os.path.join(conf.REGEX_FOLDER_OUTPUT, project_name)
        if remove_project:
            shutil.rmtree(self.project_folder, ignore_errors=True, onerror=None)
        if not os.path.exists(self.project_folder):
            create_folder(self.project_folder)

    def run_with_benign_check(self, _cluster_dict, benign_list, benign_for_retrain=conf.BENIGN_FOR_RETRAIN,
                              round_max=15,
                              take_existing_result=False):
        """
        Main API. Extract signatures fron cluster dict and check the results on a benign list
        :param _cluster_dict: Ex: {'cluster_1': {'match': ['pandas', 'gibbon'], 'unmatch': ['monkey']}
        :param benign_list: list of path to not match
        :param benign_for_retrain: benign to be added for the regex generation process on each step
        :param round_max: Max round for generating the regexes. If -1, stop until no FP is found
        :param take_existing_result: Load the existing results in self.project_folder and start the round
                with the benign samples
        :return: a cluster_dict that we should pass to another round if we want to continue the process.
        """

        assert round_max >= 1
        benign_list = self.remove_nan_value_from_list(benign_list)
        n_path = sum([len(_cluster_dict[cluster]['match']) for cluster in _cluster_dict])
        if take_existing_result:
            logger.info("Loading existing signatures in folder {}".format(self.project_folder))
            cluster_result = self.get_cluster_results()
        else:
            logger.info('Extracting regex for the first time on {} cluster(s)!'.format(len(_cluster_dict)))
            cluster_result = self.run_cluster_dict(_cluster_dict)
        old_cluster_dict = _cluster_dict
        old_cluster_result = cluster_result
        cluster_sig_dict = {k: [v] for k, v in cluster_result.items()}
        _round = 0
        while len(old_cluster_dict) > 0:
            if _round == round_max:
                break
            logger.info(f'Starting Round {str(_round + 1)}')
            new_cluster_dict = self.test_cluster_dict(old_cluster_dict, old_cluster_result, benign_list,
                                                      limit=benign_for_retrain)
            if len(new_cluster_dict) == 0:
                if _round == 0:
                    logger.info("It is too good to be true. I kill the process")
                    return 'error'
            logger.info(f'Creating regexes for {str(len(new_cluster_dict))} cluster(s) : {list(new_cluster_dict)}')

            cluster_result_new = self.run_cluster_dict(new_cluster_dict)
            old_cluster_dict = new_cluster_dict

            for cluster in new_cluster_dict:
                cluster_sig_dict[cluster].append(cluster_result_new[cluster])
            _round += 1
            old_cluster_result = cluster_result_new
        last_cluster_dict = self.test_cluster_dict(_cluster_dict, self.get_cluster_results(), benign_list,
                                                   limit=1000000)
        cluster_with_no_fp = {k: _cluster_dict[k] for k in set(_cluster_dict) - set(last_cluster_dict)}
        fp_stat = ""
        no_fp_cluster = []
        for cluster in cluster_result:
            if cluster in last_cluster_dict:
                fp_rate = round(len(last_cluster_dict[cluster]['unmatch']) * 100 / len(benign_list), 3)
                fp_stat += f""" {cluster} - {str(len(last_cluster_dict[cluster]['unmatch']))} FP ( {fp_rate} % """
                fp_stat += '\n'
            else:
                no_fp_cluster.append(cluster)
        n_path_no_fp = sum([len(cluster_with_no_fp[k]['match']) for k in cluster_with_no_fp])
        cluster_path_stat = ''
        for cluster in dict(sorted(cluster_sig_dict.items(), key=lambda x: len(x[1]))):
            cluster_path_stat += f'{cluster} : ' + ' ---> '.join(cluster_sig_dict[cluster]) + '\n'
        summary_stat = f"""
        #### Summary ####
        
        Init\n:
        N cluster : {len(_cluster_dict)}
        N paths: {str(n_path)} 
        N benign in final test: {len(benign_list)}
        Benign number for retraining : {benign_for_retrain}
        N round: {round_max}
        
        Cluster sig paths: 

        {cluster_path_stat}

        After final testing: 
        Cluster with 0 FP: {set(cluster_with_no_fp)} 
        Number of paths covered with 0 FP: {n_path_no_fp} 
        Percentage of paths covered with 0 FP: {round(100 * n_path_no_fp / n_path, 2)} %
        
        ### FP Report ###

        With FP :
        
        {fp_stat}
        
        Without:
        
        {no_fp_cluster}
        
        """
        logger.info(summary_stat)
        return last_cluster_dict

    def test_cluster_dict(self, _cluster_dict, cluster_result, benign_list, limit=10):
        """

        :param _cluster_dict: cluster_dict
        :param cluster_result: cluster result. Ex {'cluster_1': 'a{3}b+'}
        :param benign_list: list of benign
        :param limit: int. Stop testing after limit catches
        :return: a cluster_dict that contains only the cluster that have FP.
        """
        new_cluster_dict = {}
        for cluster in _cluster_dict:
            benign_match = self.check_regex_list(cluster_result[cluster],
                                                 list(set(benign_list) - set(_cluster_dict[cluster]['unmatch'])),
                                                 limit=limit)[1]

            if len(benign_match) == 0:
                logger.info(
                    'Signature on cluster {} ( {}) has no benign match !'.format(cluster, cluster_result[cluster]))
                continue
            logger.info('{} benign match in {}'.format(len(benign_match), cluster))
            new_cluster_dict[cluster] = {'match': _cluster_dict[cluster]['match'],
                                         'unmatch': benign_match + _cluster_dict[cluster]['unmatch']}
        return new_cluster_dict

    def run_cluster_dict(self, _cluster_dict):
        """
        Run regex extraction from a cluster dict
        :param _cluster_dict: cluster dict
        :return: cluster results
        """
        for cluster in _cluster_dict:
            logger.info(f'Creating regex for cluster {cluster}')
            self.create_regex(_cluster_dict[cluster]['match'], cluster_name=cluster,
                              str_to_not_match=_cluster_dict[cluster]['unmatch'])
        cluster_results = self.get_cluster_results()  # Here we load all the results !
        logger.info(f'Cluster results {cluster_results}')
        return cluster_results

    def create_regex(self, str_list, cluster_name, str_to_not_match=None):
        """
        Create regex from a string list and list to not match
        :param str_list: list
        :param cluster_name: str
        :param str_to_not_match: list
        :return: void
        """
        str_to_not_match = self.remove_nan_value_from_list(str_to_not_match)
        json_path = self.create_json_cluster([x + '.' for x in str_list], [x + '.' for x in str_to_not_match],
                                             name=cluster_name)
        self.run_regex_extraction(json_path, output_folder=conf.REGEX_TMP)
        self.__move_results(cluster_name)

    def __move_results(self, cluster_name):
        """
        Move results from tmp to the folder of the project
        :param cluster_name: name of the cluster
        :return: void
        """
        output_file = os.listdir(conf.REGEX_TMP)[0]
        shutil.move(os.path.join(conf.REGEX_TMP, output_file),
                    os.path.join(self.project_folder, 'results_' + cluster_name + '.json'))

    def get_cluster_results(self):
        """
        Parse the results outputed by the regex creation process
        :return: cluster results
        """
        results = {}
        for file in os.listdir(self.project_folder):
            if not file.startswith('results'):
                continue
            file_splitted = file.split('_')

            cluster_name = '_'.join([file_splitted[1], file_splitted[2], file_splitted[3]]).replace(".json", "")
            with open(os.path.join(self.project_folder, file)) as json_file:
                cluster_result = json.load(json_file)
                # results[cluster_name] = cluster_result['bestSolution']["solutionJS"]
                results[cluster_name] = cluster_result['bestSolution']["solution"]
        return results

    @staticmethod
    def run_regex_extraction(json_to_extract, output_folder=conf.REGEX_TMP,
                             mem=round(virtual_memory().available / 10 ** 9) * 1000, threads=None):
        """
        Run the Java process that creates the regex
        :param json_to_extract: json
        :param output_folder: output folder
        :param mem: memory to use. By default almost all the memory available
        :param threads: number of threads. For example mp.cpu_count(). /!\ Can create memory issue
        :return: void
        """

        args = ['java', '-Xmx{}M'.format(mem), '-Xms{}M'.format(int(mem / 2)), '-jar', conf.REGEX_JAVA, "-d",
                json_to_extract, "-o", output_folder]
        if threads:
            args += ["-t", str(threads)]
        try:
            logger.info(f'Running subprocess with input {json_to_extract}')
            subprocess.run(args)
        except subprocess.TimeoutExpired:
            print(f'Timeout reached for input {json_to_extract}')  # it should not take more than 1 hour

    def create_json_cluster(self, str_to_match, str_to_not_match=None, name='urls_cluster', description='luda'):
        """
        Create the input for the Java process
        :param str_to_match: list of str
        :param str_to_not_match: list of str
        :param name: name of the json
        :param description: str
        :return: path where the json was created
        """
        examples = []
        for el in str_to_match:
            examples.append({
                "string": el,
                "match": [{"start": 0, "end": len(el) - 1}],
                "unmatch": []})
        if len(str_to_not_match) > 0:
            for el in str_to_not_match:
                examples.append({
                    "string": el,
                    "match": [],
                    "unmatch": [{"start": 0, "end": len(el) - 1}]})

        result = {
            "name": name,
            "description": description,
            "regexTarget": "",
            "examples": examples}
        json_path = os.path.join(self.project_folder, 'input_' + name + '.json')
        with open(json_path, 'w') as f:
            json.dump(result, f)
        return json_path

    @staticmethod
    def check_regex_list(sig, path_list, limit=9999999):
        """
        Check a regex against of list of str
        :param sig: str
        :param path_list: list
        :param limit: int
        :return: tuple
        """
        match = 0
        urls_match = []
        batch_size = conf.TEST_BATCH_SIZE
        for i in range(0, len(path_list), batch_size):
            if match > limit:
                break
            batch = path_list[i:i + batch_size]
            # res = js_regex.compile(sig).search(r'{}'.format(path))
            result_list = Regex.run_regex_java(sig, batch)
            for j, match_bool in enumerate(result_list):
                if match >= limit:
                    break
                if not match_bool:
                    continue
                detected_path = path_list[i + j]
                if match < 2:  # We want to print only some examples
                    # logger.info('Match on {}'.format(res.group(0)))
                    logger.info('Match on {}'.format(detected_path))
                urls_match.append(detected_path)
                match += 1

        return match, urls_match

    def create_result_report(self, output_file=None):
        if not output_file:
            output_file = os.path.join(self.project_folder, f'report_{self.project_name}.csv')
        list_of_dict = list()
        for file in os.listdir(self.project_folder):

            if 'results' in file:
                with open(os.path.join(self.project_folder, file)) as json_file:
                    cluster_result = json.load(json_file)
                with open(os.path.join(self.project_folder, file.replace('results', 'input'))) as json_file:
                    cluster_input = json.load(json_file)
                    malicious = 0
                    benign = 0
                    example_to_keep = None
                    for example in cluster_input['examples']:
                        if len(example['match']) > 0:
                            if not example_to_keep:
                                example_to_keep = example['string']
                            malicious += 1
                        else:
                            benign += 1
                tmp = {'name': file.replace('results_', '').replace('.json', ''),
                       'regex_js': cluster_result['bestSolution']['solutionJS'],
                       'regex_java': cluster_result['bestSolution']['solution'],
                       'malicious': malicious,
                       'benign': benign,
                       'round': benign // conf.BENIGN_FOR_RETRAIN,
                       'example_malicious': example_to_keep,
                       'results_file': file,
                       'input_file': file.replace('results', 'input')}
                list_of_dict.append(tmp.copy())
        df = pd.DataFrame(list_of_dict)
        df.to_csv(output_file)
        return df

    @staticmethod
    def run_regex_java(regex, list_string):
        """
        Run Regex on list of string with Java code
        :param regex: regex Java
        :param list_string: string to test
        :return: list of String ie ['true', 'false', 'false']
        """
        with open(conf.INPUT_REGEX_RUNNER, 'w') as f:
            json.dump({'to_test': [x for x in list_string if str(x) != 'nan']}, f)
        command = ['java', '-jar', conf.REGEX_RUNNER, regex, conf.INPUT_REGEX_RUNNER, conf.OUTPUT_REGEX_RUNNER]
        try:
            subprocess.run(command, stdout=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            print(f'Timeout reached for regex {regex}')  # it should not take more than 1 hour !
        with open(conf.OUTPUT_REGEX_RUNNER, 'r') as f:
            result = json.load(f)

        return result['results']

    @staticmethod
    def remove_nan_value_from_list(_list):
        result = []
        for el in _list:
            if str(el) == 'nan':
                logger.warning('You have nan value in your list !!. List extract {}'.format(_list[:3]))
                continue
            result.append(el)
        return result

