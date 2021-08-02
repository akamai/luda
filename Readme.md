[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)
![Coverage](test/coverage.svg "Coverage")


# LUDA: Large URLs Dataset Analyzer for security


_Presented at [BlackHat USA 2021 Arsenal](https://www.blackhat.com/us-21/arsenal/schedule/index.html#luda--large-urls-dataset-analyzer-for-security-23851
)_ 

# Table of Contents
1. [Download and getting started](#Download-and-getting-started)
2. [The 5 modules](#The-5-modules)
    1. [Data](#Data)
    2. [Feeders](#Feeders)
    3. [Preprocessing](#Preprocessing)
    4. [Clustering](#Clustering)
    5. [Regex generation](#Regex-generation)
3. [Deployment with docker to a remote machine](#Deployment-with-docker-to-a-remote-machine)
4. [Support and contributing to Luda](#Support-and-contributing-to-Luda)


Malicious actors often reuse code to deploy their malware, phishing website or CNC server. As a result, similiaries can 
be found on URLs path by inspecting internet traffic. Moreover, deep learning models or even regular ML model do not 
fit for inline deployment in terms of running performance. However, regexes ( or YARA rules ) can be deployed on a proxy
and work in real time on all the traffic. LUDA can take a set of malicious and benign URLs and return a list of regexes
ready to be deployed inline ! 

# Download and getting started 

First of all, clone the repo :)


To make sure it will work for everyone, we will run everything inside a docker. Assuming you have docker 
and docker-composed on your machine,
just run from the project directory

```bash
docker-compose up  #building the docker for the first time can take few minutes.
```

It will create a container named luda as well as running a jupyter notebook that you can access on localhost:5555 (token: luda). 
You noticed that it created also a folder "data" on project level that is mapped to the same folder on the docker. 

So now copy (on the host) test/data_demo.csv to data/data_demo.csv. The file conf.json is already set like we need.

Now go to you docker with 
```bash
docker exec -it luda bash
```
and run
```bash
python main.py #should take less than 1 min with 8cpu 16go RAM
```

It will preprocess the data, and cluster the urls. Now let's look at the clusters !
Go to you localhost:5555 to access the jupyter notebook hosted on the docker and open analysis/luda_analysis.ipynb

You can run all cells adn then go to the last part "Cluster analysis". The last output cells should show you the clusters.
You should see something like this

```text
Name: cluster, dtype: int64
#####Cluster 0 - 27 samples: #### 

['/neat/serverphp/config.bin',
 '/serverphp/config.bin',
...
 '/pus1/serverphp/config.bin',
 '/lg/server.php/config.bin',
 '/ekene/Severphp/config.bin',
 '/server[php]/config.bin',
 '/versy/serverphp/config.bin']


#####Cluster 4 - 17 samples: #### 

['/mupanel/post.php',
 '/jiz/kbpanel/post.php',
...
 '/low/kbpanel/post.php',
 '/1/kbpanel/post.php',
 '/new/kbpanel/post.php']
```

Here you can choose from which cluster you would like to run the regex generation. This last part is CPU and RAM expensive and you should run
it only on the clusters that looks "good". Here you can also identify path that can generate FP ( like "/index.php" for example. Check use_case_clustering.py to see how you can fix FP at this step).
Let's say you choose only those two clusters (0 and 4). Change the config.json (on the docker, you can access it directly via the notebook)
to be 

```json
{
  "main_file": "data_demo.csv",
  "data": {
    "run": false,
    "additional_files": [
      {
        "path": "my_data/benign_data.csv",
        "label": "benign"
      },
      {
        "path": "my_data/malicious_traffic.csv",
        "label": "malicious"}
    ]
  },
  "feeder": {
    "run": false,
    "sources": [
      "urlhaus",
      "openfish",
      "alexa"
    ]
  },
  "preprocessing": {
    "run": false,
    "name": "basic"
  },
  "clustering": {
    "run": false,
    "preprocessed_file": null,
    "skip_distance_computation": false,
    "clusterer": {
      "dbscan": {
        "eps": 20,
        "min_samples": 8
      }
    },
    "metric": "sw",
    "features_folder": "luda_output/mymatrix",
    "filter_similarity": 30,
    "phishing_mode": false
  },
  "regex": {
    "run": true,
    "benign_for_retrain": 30,
    "round_max": 10,
    "regex_folder": "myregexes",
    "take_existing_result": true,
    "min_path_for_run": 200,
    "cluster_list": [0,4]
  }
}
```

We just turned off all step exept the regex generation steps that we want to run. We also added that we want run on cluster
0 and 4 only.

Now again (from the docker)

```bash
python main.py
```

Check the log on luda_output/logs/luda.log at the end you can see a small report

```txt



```

Congrats on your first LUDA run. You now have 2 (Java) regex that can be used malicious urls belonging to the clusters you found :)

On the next part, we will dive into LUDA architecture to understand each of its components, understand what else you can do and possibly make 
you contribute to the project !




LUDA is composed of **5  modules** : data, feeder, preprocessing, clustering and regex generation. 

To run LUDA, we need to first configure _config.json_

# The 5 modules

Every part is independent and can be run separately with the config file.

## Data


To provide LUDA with some URLs, you can pass some files. The **only condition** that they should have is a column named "url".

LUDA will then load them and store it in its format joined with the data coming from the feeders. By default, it will look for the file
in the data folder. Otherwise you can write an absolute path. 
The main file does not have to exists. You can add you own file in additional_files and luda will combine them.

```json
"main_file": "data_demo.csv",
  "data": {
    "run": false,
    "additional_files": [
      {
        "path": "my_data/benign_data.csv",
        "label": "benign"
      },
      {
        "path": "my_data/malicious_traffic.csv",
        "label": "malicious"}

    ]
  },
```

## Feeders

We implemented several feeders from malicious sources that bring you the most recent data. Among them feeders for UrlHaus,
OpenPhish, Alexa, Majestic, VT etc. If a your feeder bring domains (not URLs) a crawler is available and can convert your domain
into URLs. We invite you to create your own feeder and share it to this project 

```json
  "feeder": {
    "run": false,
    "sources": [
      "urlhaus",
      "openfish",
      "alexa"
    ]
  }

```

## Preprocessing

To get better results and save computation, it is *mandatory* to preprocess the data. You need to filter smartly 
your URLs to leave only the one that "have a chance to create a cluster". 

We provide a class that implemented "basic" preprocessing techniques that we are currently using.

```json
  "preprocessing": {
    "run": false,
    "name": "basic"
  }
```

## Clustering 

```json
  "clustering": {
    "run": false,
    "preprocessed_file": null,
    "skip_distance_computation": false,
    "clusterer": {
      "dbscan": {
        "eps": 20,
        "min_samples": 8
      }
    },
    "metric": "sw",
    "features_folder": "luda_output/mymatrix",
    "filter_similarity": 30,
    "phishing_mode": false
  }
```

### Distance matrix computation


This is a CPU and RAM expensive step. It will use ( by default ) all your CPU and can catch 300GB RAM for a list of URLs 
longuer than 35k...That's why the preprocessing step is very important. At the end of the task, it will save the results 
in a folder ( specified in the config file) that you can reuse several times to test different parameters of the clustering.

If you already have a csv file with your data. You need to write its **absolute** path in config.json in "preprocessed_file" 


### Clustering algorithm

We are currently using DBscan since we want to control MinPoints ( minimum points in a cluster). Moreover, since we build
by ourselves the metric, we understand what is Epsilon ! Setting Epsilon to 20 for example is equivalent 
to say "Group together URLs that are 80% similar"


This **step in quick**, you can run it several time to test different parameters

## Regex generation

For this step, we use an existing research. The original code can be found here https://github.com/MaLeLabTs/RegexGenerator

We already added to LUDA the dependencies that we need from this project. More details on this repo to optimize the regex generation process.

We strongly advise you to first look at your cluster that you got from the clustering part before running on all your clusters.
Once you chose your cluster, add their id to "cluster_list"
```json
  "regex": {
    "run": true,
    "benign_for_retrain": 30,
    "round_max": 10,
    "regex_folder": "myregexes",
    "take_existing_result": false,
    "min_path_for_run": 200,
    "cluster_list": [0,4]
  }

```

This is an example of the final report you can get when running test/data_demo.csv


```txt
        N paths: 64
        N benign in final test: 9486
        Benign number for retraining : 30
        N round: 10

        Cluster sig paths:

        cluster_27_0 : (\.*+[^_])++ ---> [^bin]++[^\.]++\.bin
cluster_12_15 : [^php]*+php ---> /\w\w++/gate\.php ---> /\w\w\w\w\d/gate\.php
cluster_8_16 : ([^_]\w++)++ ---> [^php]++php ---> /\w++/PHP/\w++\.php
cluster_17_4 : ([^_]\w++)++ ---> [^\.]*+\.php ---> /\w++(?:/kbpanel)?+/post\.php ---> [^php]*+\w\w\w/?+\w++/post\.php


        After final testing:
        Cluster with 0 FP: {'cluster_8_16', 'cluster_17_4', 'cluster_27_0', 'cluster_12_15'}
        Number of paths covered with 0 FP: 64
        Percentage of paths covered with 0 FP: 100.0 %

        ### FP Report ###

        With FP :



        Without:

        ['cluster_12_15', 'cluster_8_16', 'cluster_27_0', 'cluster_17_4']
```


# Deployment with docker to a remote machine

Getting an environmment ready can be achieved with 

```bash
docker-compose up
```

By default this docker create a container named **luda** and build an image called **luda_image** . The docker run also 
a Jupyter Notebook that you can access from the port 5555 (5555 is mapped to 8888 in this version)

One of the most efficient way to run LUDA in another machine is to send **luda_image** to a Docker registry and pull directly
on the target machine

On local you can run 

```bash
docker-compose build # to create the image
docker tag luda_image:latest your_docker_user/luda_image 
docker push your_docker_user/luda_image 
```

and on the remote you can either run it with docker-compose (you need to it copy it there) or run

```bash
docker rm -f luda; sudo docker run -it -v /home/data/:/code/data -p 5555:8888 --name luda your_docker_user/luda_image bash

# We first delete luda in case of the container already exists. It will delete all the container including your notebook.
# and inside it you can launch the jupyter notebook if you want (inside a screen so it stay alive if you close the tab)

screen -d -m -S jupyter jupyter notebook --allow-root --no-browser --ip 0.0.0.0 --NotebookApp.token='luda'
```
Then you just need to send your data 

```bash
scp -i yourkey.pem data_preprocessed.csv user@your_powerfull_machine:/home/data # remember we map home/data to code/data 
```
An advantage to send your data separately is first to not get a big docker image and also to update your code if needed
and still test with your data since the docker volume is mapped into a persistent folder in the host machine
/!\ If you add your data to your Docker, after several tries, your disk might be full. 
You can delete all images by running

```bash
docker rmi -f $(docker images -a -q)
```


If you always need "sudo" to run docker command, you can just your user to the docker group by running

```bash
sudo usermod -a -G docker [user]
newgrp docker
```
## Access the remote Jupyter Notebook

Once you are your container running, you can either access the Jupyter notebook via your browser on port 5555 of your server

OR you can do SSH tunneling ( if your machine does not have open port for inbound connection)
```bash
ssh -N -f -L localhost:<FREE PORT IN YOUR LOCAL MACHINE>:localhost:5555 -i yourkey.pem user@your_powerfull_machine 
```


# Support and contributing to Luda

This code is maintained. You are welcome to ask any questions directly on Git. We will try to answer as quick as possible.

We also invite your to contribute to this open source. Add your feeders, preprocessing techniques, clustering algorithms
or fix bugs. 
It can be done via pull request. More details on how to pull request [here](https://www.dataschool.io/how-to-contribute-on-github/
). Please provide basic test with your code.

## Running the tests

Adding test protect your code but also explain them to others.
Make sure the project as at least 70% coverage.
To check the coverage, pip install those 2 packages

```bash
pip install coverage
pip install coverage-badge
```
and run from the main luda directory

```bash
coverage run -m pytest
coverage report -m --omit="*/test*" # optional - to see the coverage without including tests
coverage-badge -o test/coverage.svg -f # this will create the coverage badge loaded in the Readme
```
# Authors

**Code**: [Jordan Garzon]
**Algorithm**: [Jordan Garzon] and [Asaf Nadler]

from Akamai Technologies


[Jordan Garzon]: https://twitter.com/JordGarzon
[Asaf Nadler]: https://twitter.com/AsafNadler

```text
               |||      |||    
               | |  __  | |
|-|_____-----/   |_|  |_|   \-----_____|-|
|_|_________{   }|  (^) |{  }__________|_|  
 ||          |_| |   ^  | |_|          ||  
 |              \|  /\  |/              |  
 |               \ |--| /               |    
 =               \ |__| /               =    
 +               \      /               +   ENJOY !
                  \    /    
                  \    /    
                   \  /
                   \  /
                   \  /
                   \  /
                   \  /    
                   \  /
                    \/

```