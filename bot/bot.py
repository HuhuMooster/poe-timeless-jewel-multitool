from queue import Queue
from pymongo import MongoClient
from datetime import datetime
import logging
import time
import sys
import numpy as np

from .trader import Trader
from .tree_navigator import TreeNavigator
from .utils import get_config
from .input_handler import InputHandler


class Bot:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.log = logging.getLogger('bot')
        self.config = get_config('bot')
        self.resolution = self.split_res(self.config['resolution'])

        self.trader = Trader(self.resolution)
        self.input_handler = InputHandler(self.resolution)
        self.db = MongoClient(self.config['db_url'])[self.config['db_name']]
        self.run = True

    def loop(self):
        time.sleep(5)
        while self.run:
            username = 'N/A'
            # To enable the trading, uncomment rows below
            '''
            empty = self.trader.verify_empty_inventory()
            if not empty:
                self.trader.stash_items()
            username = self.trader.wait_for_trade()
            successfully_received = self.trader.get_items(username)
            if not successfully_received:
                continue
            '''
            jewel_locations, descriptions = self.trader.get_jewel_locations()
            self.log.info('Got %s new jewels' % len(jewel_locations))
            long_break_at_idx = np.random.choice(60, 5)
            for idx, jewel_location in enumerate(jewel_locations):
                self.log.info('Analyzing jewel (%s/%s) with description: %s'
                              % (idx, len(jewel_locations), descriptions[idx]))
                if idx in long_break_at_idx:
                    self.log.info('Taking a break of around 5 minutes.')
                    self.input_handler.rnd_sleep(mean=300000, sigma=100000, min=120000)
                stored_equivalents = self.db['jewels'].find({'description': descriptions[idx]})
                if stored_equivalents.count() > 0:
                    self.log.info('Jewel with descriptions %s is already analyzed, skipping!' % descriptions[idx])
                    continue
                self.tree_nav = TreeNavigator(self.resolution)
                analysis_time = datetime.utcnow()
                name, description, socket_instances = self.tree_nav.eval_jewel(jewel_location)
                self.log.info('Jewel evaluation took %s seconds' % (datetime.utcnow() - analysis_time).seconds)
                for socket in socket_instances:
                    socket['description'] = description
                    socket['name'] = name
                    socket['created'] = analysis_time
                    socket['reporter'] = username

                self.store_items(socket_instances)

            # To enable the trading, uncomment row below
            #self.trader.return_items(username, jewel_locations)

    def store_items(self, socket_instances):
        result = self.db['jewels'].insert_many(socket_instances)
        return result

    def split_res(self, resolution):
        resolution = [int(n) for n in resolution.split('x')]
        return resolution
