# Description: Store objects to communicate with the DB to acquire golf stats.
# Author: Michael Krakovsky

from sys import path
path.extend('../../../../')                      # Import the entire project.
from My_Golf_Journey.config import mongo_config
from pymongo import MongoClient
from pandas import DataFrame, to_numeric
from numpy import float16

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

        df = DataFrame(list(self.collection.aggregate([
            {"$match": {"courseSnapshots.courseGlobalId": course_id}},
            {"$unwind": "$scorecardDetails"},
            {"$sort": {"scorecardDetails.scorecard.startTime" : 1}},
            {"$unwind": "$scorecardDetails.scorecard.holes"}, 
            {"$group": {"_id": "$scorecardDetails.scorecard.holes.number",
                "scoring_average": {"$avg": "$scorecardDetails.scorecard.holes.strokes"}}}, 
            {'$sort': {"_id": 1}}
        ])))
        df = df.set_index('_id')
        return df.join(self.get_hole_pars(course_id))

    def get_hole_pars(self, course_id, holes=18):

        """
        Function Description: Get the par of each hole on a course.
        Function Parameters: course_id (Int: The course Id.), holes (Int: The number of holes completed in the round.)
        Function Throws: Nothing
        Function Returns: (Dataframe: A dataframe of all holes and there respective pars.)
        """

        hole_pars = list(self.collection.aggregate([
	        {"$match": {"courseSnapshots.courseGlobalId": course_id,
             "scorecardDetails.scorecard.holesCompleted" : holes}},
	        {"$unwind": "$courseSnapshots"},
	        {"$project": {"_id": 0, "holePars": "$courseSnapshots.holePars"}}
	        ]))[0]
        return DataFrame({hole + 1 : par for hole, par in enumerate(hole_pars['holePars'])}.items(), columns=['Hole', 'Par']).set_index('Hole').astype(float16)

    def get_fairways(self, course_id):

        """
        Function Description: Get the count of Fairways hit and missed.
        Function Parameters: course_id (Int: The course id.)
        Function Throws: Nothing
        Function Returns: (DataFrame: The organised data containing the results.)

                   outcome  hole  count
                1     LEFT     4     35
        """

        rounds = list(self.collection.aggregate([                                                                             # Filter the information pertaining to Fairways Hit.
            {
                '$match': {
                    'courseSnapshots.courseGlobalId': course_id
                }
            }, {
                '$unwind': {
                    'path': '$scorecardDetails'
                }
            }, {
                '$unwind': {
                    'path': '$scorecardDetails.scorecard.holes'
                }
            }, {
                '$group': {
                    '_id': {
                        'outcome': '$scorecardDetails.scorecard.holes.fairwayShotOutcome', 
                        'hole': '$scorecardDetails.scorecard.holes.number'
                    }, 
                    'count': {
                        '$sum': 1
                    }
                }
            }
        ]))
        new_rounds = []                                                                                                       # Clean the data for missing data.
        for el in rounds:
            if 'outcome' in el['_id']:
                new_rounds.append({'outcome': el['_id']['outcome'], 'hole': el['_id']['hole'], 'count': el['count']})
            else:
                new_rounds.append({'outcome': 'NO_ENTRY', 'hole': el['_id']['hole'], 'count': el['count']})
        rounds = DataFrame(new_rounds)
        return rounds[(rounds['outcome'] != "NO_ENTRY") & (rounds['outcome'] != "NO_FAIRWAY")]

    def get_fairway_accuracy(self, course_id):
        
        """
        Function Description: Get the Fairway Accuracy of each hole at a course.
        Function Parameters: course_id (Int: The course id of the course.)
        Function Throws: Nothing
        Function Returns: (DataFrame: The data containing the fairways hit.)

                count  HIT_Count  Accuracy
            hole                            
            1       134       61.0  0.455224

        """
        
        rounds = self.get_fairways(course_id)
        rounds = rounds[(rounds['outcome'] != "NO_ENTRY") & (rounds['outcome'] != "NO_FAIRWAY")]        # Filter out records that do not apply.
        new_rounds = rounds.groupby(by=["hole"]).sum()
        for index, row in new_rounds.iterrows():
            hit_count = int(rounds[(rounds['hole'] == index) & (rounds['outcome'] == "HIT")]['count'])
            accuracy = hit_count / int(row['count'])
            new_rounds.loc[index, 'HIT_Count'] = hit_count
            new_rounds.loc[index, 'Accuracy'] = accuracy
        new_rounds.index.names = ['_id']
        return new_rounds                                                                               # Change the index for consistency.

    def _greens_by_hole(self, course_id):

        """
        Function Description: Organise the necessary data to determine the user has hit a green.
        Function Parameters: course_id (Int: The course id to retrieve the stats.)
        Function Throws: Nothing
        Function Returns: (DataFrame: The data organised in a Pandas DataFrame.)
        """

        return DataFrame(list(self.collection.aggregate([
            {
                '$match': {
                    'courseSnapshots.courseGlobalId': course_id
                }
            }, {
                '$unwind': {
                    'path': '$scorecardDetails'
                }
            }, {
                '$unwind': {
                    'path': '$scorecardDetails.scorecard.holes'
                }
            }, {
                '$project': {
                    '_id': 0, 
                    'hole_number': '$scorecardDetails.scorecard.holes.number', 
                    'strokes': '$scorecardDetails.scorecard.holes.strokes', 
                    'putts': '$scorecardDetails.scorecard.holes.putts'
                }
            }
        ])))

    def _is_hit(self, par_df, hole_number, strokes, putts):

        """
        Function Description: Determine whether the a green was hit in regulation.
        Function Parameters: par_df (DataFrame: The hole numbers and their respective pars.), 
            hole_number (Int: The hole number where the event took place.), 
            strokes (Int: The number of strokes incurred within the hole.), 
            putts (Int: The number of putts taken on the hole.)
        Function Throws: Nothing
        Function Returns: (Boolean: True if GIR or under and False otherwise.)
        """

        hole_par = int(par_df.loc[hole_number, :]['Par'])
        if hole_par == 5:
            x = strokes - putts - 3
        elif hole_par == 4:
            x = strokes - putts - 2
        else:
            x = strokes - putts - 1
        return x <= 0

    def get_green_accuracy(self, course_id):

        """
        Function Description: Calculate the greens hit on a particular course.
        Function Parameters: course_id (Int: The course id.)
        Function Throws: Nothing
        Function Returns: (DataFrame: The accuracy of greens hit on the course.)

              hit_count	attempt	hit_percentage
            _id			
            1.0	43	135	0.318519
            
        """

        greens = self._greens_by_hole(course_id)                                               # Get the necessary prep data.
        caledon_pars = self.get_hole_pars(course_id)
        green_percentage = {}
        for _, row in greens.iterrows():
            hole_number = row['hole_number']
            strokes = row['strokes']
            putts = row['putts']
            hit = self._is_hit(caledon_pars, hole_number, strokes, putts)                      # Count the number of times the greens have been hit.
            if hole_number not in green_percentage:
                green_percentage[hole_number] = {'hit_count': 0, 'attempt': 0}
            if hit:
                green_percentage[hole_number]['hit_count'] += 1
            green_percentage[hole_number]['attempt'] += 1
        green_perct = DataFrame(green_percentage).T
        green_perct.index.names = ['_id']
        green_perct['hit_percentage'] = green_perct['hit_count'] / green_perct['attempt']
        return green_perct