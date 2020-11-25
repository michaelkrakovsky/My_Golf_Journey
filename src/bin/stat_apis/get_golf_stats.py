# Description: Store objects to communicate with the DB to acquire golf stats.
# Author: Michael Krakovsky

from sys import path
path.extend('../../../../')                      # Import the entire project.
from My_Golf_Journey.config import mongo_config
from pymongo import MongoClient
from pandas import DataFrame

class Stats():

    def __init__(self):

        """
        Class Description: Retrieve stats from the MongoDB to perform future analysis.
        Class Instantiators: Nothing
        """

        client = MongoClient(mongo_config['conn_str'])
        db = client.Golf_Stats_DB
        self.collection = db.Scorecards

    def get_putting_avg_by_hole(self, course_id):

        """
        Function Description: Get the putting average by the hole at a particular golf course.
        Function Parameters: coourse_id (Int: The unique id to identify the golf course.)
        Function Throws: Nothing
        Function Returns: (DataFrame: The collection of hole numbers and putts per hole.)
        """

        df = DataFrame(list(self.collection.aggregate([
            {"$match": {"courseSnapshots.courseGlobalId": course_id}},
            {"$unwind": "$scorecardDetails"},
            {"$sort": {"scorecardDetails.scorecard.startTime" : 1}},
            {"$unwind": "$scorecardDetails.scorecard.holes"}, 
            {"$group": {"_id": "$scorecardDetails.scorecard.holes.number",
                "putting_average": {"$avg": "$scorecardDetails.scorecard.holes.putts"}}},
            {'$sort': {"_id": 1}}
        ])))
        return df.set_index('_id')

    def get_scoring_avg_by_hole(self, course_id):

        """
        Function Description: Get the scoring average by the hole at a particular golf course.
        Function Parameters: coourse_id (Int: The unique id to identify the golf course.)
        Function Throws: Nothing
        Function Returns: (List: The collection of hole numbers and putts per hole.)
        """

        return list(self.collection.aggregate([
            {"$match": {"courseSnapshots.courseGlobalId": course_id}},
            {"$unwind": "$scorecardDetails"},
            {"$sort": {"scorecardDetails.scorecard.startTime" : 1}},
            {"$unwind": "$scorecardDetails.scorecard.holes"}, 
            {"$group": {"_id": "$scorecardDetails.scorecard.holes.number",
                "scoring_average": {"$avg": "$scorecardDetails.scorecard.holes.strokes"}}}, 
            {'$sort': {"_id": 1}}
        ]))



tester = Stats() 