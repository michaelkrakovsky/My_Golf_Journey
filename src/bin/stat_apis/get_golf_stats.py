# Description: Store objects to communicate with the DB to acquire golf stats.
# Author: Michael Krakovsky

from sys import path
path.extend('../../../../')                      # Import the entire project.
from My_Golf_Journey.config import mongo_config
from pymongo import MongoClient

class Stats():

    def __init__(self):

        """
        Class Description: Retrieve stats from the MongoDB to perform future analysis.
        Class Instantiators: Nothing
        """

        client = MongoClient(mongo_config['conn_str'])
        db = client.Golf_Stats_DB
        self.collection = db.Scorecards

tester = Stats() 