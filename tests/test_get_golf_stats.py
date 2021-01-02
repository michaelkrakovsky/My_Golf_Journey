# Script Description: Unit testing for the API which retrieves stats from the MongoDB database.


import unittest
from sys import path
path.extend('../')                                                        # Import the entire project.
from My_Golf_Journey.src.bin.stat_apis.get_golf_stats import Stats

class Test_Get_Golf_Stats(unittest.TestCase):        

    def setUp(self):
        
        self.s = Stats()

    def tearDown(self):

        pass

    def test__is_hit(self):

        """
        Unit Test the '_is_hit method that determines whether a green is hit in regulation.
        """
        
        caledon_pars = self.s.get_hole_pars(17772)                # Get the pars of Caledon Woodself.s.
        
        self.assertFalse(self.s._is_hit(caledon_pars, 1, 4, 1))
        self.assertTrue(self.s._is_hit(caledon_pars, 1, 4, 2))
        self.assertTrue(self.s._is_hit(caledon_pars, 1, 3, 1))
        self.assertTrue(self.s._is_hit(caledon_pars, 1, 3, 2))

        self.assertFalse(self.s._is_hit(caledon_pars, 3, 5, 3))
        self.assertTrue(self.s._is_hit(caledon_pars, 3, 3, 2))
        self.assertFalse(self.s._is_hit(caledon_pars, 3, 3, 1))
        self.assertFalse(self.s._is_hit(caledon_pars, 3, 2, 0))
        self.assertTrue(self.s._is_hit(caledon_pars, 3, 2, 1))

    def test_get_fairways(self):

        """
        Unit Test get_fairways to smoke test some fairway hit calculationself.s.
        """

        query = [
                    {
                        '$match': {
                            'courseSnapshots.courseGlobalId': 17772
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
                        '$match': {
                            'scorecardDetails.scorecard.holes.number': 1, 
                            'scorecardDetails.scorecard.holes.fairwayShotOutcome': 'HIT'
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
                ]
        results = list(self.s.get_aggregate(query))                             # Sample format: [{'_id': {'outcome': 'HIT', 'hole': 1}, 'count': 61}]
        self.assertEqual(len(results), 1)
        df = self.s.get_fairways(17772)
        row = df.loc[(df['outcome'] == 'HIT') & (df['hole'] == 1)]
        self.assertEqual(results[0]['count'], row.iloc[0]['count'])

if __name__ == '__main__':
    
    try:
        unittest.main()
    except:
        pass
    print('\n\n')