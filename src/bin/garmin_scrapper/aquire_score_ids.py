# Script Description: Retrieve the score card ids from the Garmin website.
# Script Version: 0.1
# Script Author: Michael Krakovsky 


from sys import path
path.extend('../../../')                                                                    # Import the entire project.
from My_Golf_Journey.config import garmin_info

print(garmin_info['score_card_id'])
#https://connect.garmin.com/modern/profile/433ae1d7-ba04-4209-bfa4-4814c426397d/scorecards