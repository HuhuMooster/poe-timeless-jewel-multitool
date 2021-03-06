import yaml
import os
import time
import json
import numpy as np

from pymongo import MongoClient
from tqdm import tqdm


def get_config(module_name):
    config_path = os.path.abspath('config.yml')
    config = yaml.safe_load(open(config_path, 'r'))
    return config[module_name]

def rebuild_mean_mod_json(db):
    all_mods = {}
    jewel_instances = db['jewels'].find({})

    for jewel in tqdm(jewel_instances):
        for mod in jewel['summed_mods']:
            if mod in all_mods:
                all_mods[mod].append(jewel['summed_mods'][mod])
            else:
                all_mods[mod] = [jewel['summed_mods'][mod]]

    mean_mods = {}
    for mod in all_mods:
        mean_mods[mod] = np.mean(all_mods[mod])

    json.dump(mean_mods, open('data/mean_mod_values.json', 'w'))
