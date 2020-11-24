db.getCollection("Scorecards").aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$match: {
			    // enter query here
			    "courseSnapshots.courseGlobalId": 17772,
			    "scorecardDetails.scorecard.holesCompleted" : 18
			}
		},

		// Stage 2
		{
			$unwind: {
			    path: "$scorecardDetails"
			}
		},

		// Stage 3
		{
			$sort: {
			    "scorecardDetails.scorecard.startTime" : 1
			}
		},

		// Stage 4
		{
			$project: {
			  "_id": 0,
			  "Date": "$scorecardDetails.scorecard.startTime",
			  "putts": "$scorecardDetails.scorecardStats.round.putts",
			  "strokes": "$scorecardDetails.scorecard.strokes",
			}
		},

	]

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
