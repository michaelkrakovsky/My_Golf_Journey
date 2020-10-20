# Script Description: Retrieve the score card ids from the Garmin website.
# Script Version: 0.1
# Script Author: Michael Krakovsky 


from sys import path
path.extend('../../../')                                                                    # Import the entire project.
from My_Golf_Journey.config import garmin_info, exe_paths, mongo_config
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from re import findall
from time import sleep
from pymongo import MongoClient
from json import loads

username_field = '//input[@name="username"]'
password_field = '//input[@name="password"]'
submit_button = '//button[@id]'
frame = '//iframe'
gen_url = "https://connect.garmin.com/signin/"
score_url = 'https://connect.garmin.com/modern/profile/433ae1d7-ba04-4209-bfa4-4814c426397d/scorecards'
source_data_location = Path(__file__).absolute().parent.parent.parent / 'data' / 'score_card_source.txt'
log_file = Path(__file__).absolute().parent.parent.parent.parent / 'logs' / 'score_card_source_logs.txt'

def connect_to_scorecards_collection():

    """
    Function Description: Connecto the scorecards collections.
    Function Parameters: Nothing
    Function Throws: Nothing
    Function Returns: (Collection: The MongoDB connection.)
    """

    client = MongoClient(mongo_config['conn_str'])
    client.list_database_names()
    db = client.Golf_Stats_DB
    return db.Scorecards

def enter_text_w_xpath(xpath, val, driver):

    """
    Function Description: Enter text into an input field given the xpath.
    Function Parameters: xpath (String: The xpath of the element.),
        val (String: The value to be entered.),
        driver (WebBrowser: The Chrome browser we are controlling.)
    Fucntion Throws: Nothing
    Function Returns: Nothing
    """

    e = driver.find_element_by_xpath(xpath)
    e.send_keys(val)

def login_garmin(get_scorecard_ids=False):

    """
    Function Description: Login into the Garmin Website.
    Function Parameters: get_scorecard_ids (Boolean: An indication to record the known scorecard ids.)
    Function Throws: Nothing
    Function Returns: driver (Webdriver: The webdriver to navigate throughout Selenium.)
    """

    
    driver = webdriver.Chrome(executable_path=exe_paths['sel_driver'])            # Open session.
    driver.get(gen_url)
    sleep(3)                                                                      # Switch into frame.
    iframe = driver.find_element_by_xpath(frame)
    driver.switch_to.frame(iframe)
    enter_text_w_xpath(username_field, garmin_info['username'], driver)           # Enter credentials.
    enter_text_w_xpath(password_field, garmin_info['password'], driver)
    driver.find_element_by_xpath(submit_button).click()

    if get_scorecard_ids:
        sleep(12)
        driver.get(score_url)                                                     # Go to score cards.
        sleep(10)
        source = driver.page_source                                               # Dump page into file for parsing. This will contain our scorecard ids.
        with open(source_data_location.absolute(), 'w+', encoding='utf-8') as f:
            f.write(source)
    return driver

def parse_score_card_ids():

    """
    Function Description: Parse the page source to retrieve all the scorecard ids on a particular page.
    Function Parameters: Nothing
    Function Throws: Nothing
    Function Returns: (List: The score card ids that are retrieved.)
    """

    with open(source_data_location, 'r', encoding='utf-8') as f:
        text = f.read()
    ids = findall("data-scorecard-id=\"\\d*\"", text)
    return [int(findall("\\d\\d*", id)[0]) for id in ids]

def check_scorecard(id, mongo_conn):

    """
    Function Description: Check to see if the scorecard exists in the DB.
    Function Parameters: id (Int: The id of the scorecard from Garmin we are inserting.),
        mongo_conn (Collection: The connection to the Mongo Collection.)
    Function Throws: Nothing
    Function Returns: (Boolean: True if the scorecard exists and False otherwise.) 
    """

    scorecard = mongo_conn.find_one({"scorecardDetails.scorecard.id":id})
    if scorecard == None:
        return False
    return True

def insert_scorecard(json_text, mongo_conn):

    """
    Function Description: Add scorecard information into the Mongo Database.
    Function Parameters: json_text (JSON: The json dictionary containing our desired information.),
        mongo_conn (Collection: The connection to the Mongo Collection.)
    Function Throws: Nothing
    Function Returns: (Boolean: True or False depending on if the information is inserted.)
    """
    
    try:
        post = loads(json_text)
    except:
        with open(log_file, 'w+') as f:
            f.write(str(json_text))
            raise ValueError("Unable to insert Object into Mongo DB. Check the log file at {}.".format(log_file.absolute()))
    mongo_conn.insert_one(post).inserted_id
    return True

def get_scorecard_info(get_scorecard_ids):
    
    """
    Function Description: Retrieve the scorecard and game information from all the scorecard ids.
    Function Parameters: get_scorecard_ids (Boolean: An indication to record the known scorecard ids.)
    Function Throws: Nothing
    Function Returns: (Boolean: True or False depending on the behavior of our script.)
    """

    collection = connect_to_scorecards_collection()
    driver = login_garmin(get_scorecard_ids=get_scorecard_ids)
    sleep(10)                                                      # Wait prior to starting to parse the next score card.
    # Sample Link: https://connect.garmin.com/modern/proxy/gcs-golfcommunity/api/v2/scorecard/detail?scorecard-ids=155069236&include-next-previous-ids=true&user-locale=en
    ids = parse_score_card_ids()
    url = 'https://connect.garmin.com/modern/proxy/gcs-golfcommunity/api/v2/scorecard/detail?scorecard-ids={}&include-next-previous-ids=true&user-locale=en'  
    counter = 0
    for id in ids:
        is_in = check_scorecard(id, collection)               
        if not is_in:                                                 # Ensure that the scorecard does not already exist in the DB. Insert if not done already.
            driver.get(url.format(id))
            sleep(1)
            json_text = findall('{.*}', str(driver.page_source))[0]   # Retrieve only the contents within the curley brackets.
            sleep(1)
            insert_scorecard(json_text, collection)
            counter += 1
    print("We have inserted {} scorecards.".format(counter))
    return True

if __name__ == "__main__":

    result = get_scorecard_info(True)
    if result:
        print("The scorecards were retrieved from Garmin and inserted. Please check MongoDB.")
    else:
        print("The script did not retrieve the scorecard information.")