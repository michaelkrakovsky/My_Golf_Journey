# Script Description: Retrieve the score card ids from the Garmin website.
# Script Version: 0.1
# Script Author: Michael Krakovsky 


from sys import path
path.extend('../../../')                                                                    # Import the entire project.
from My_Golf_Journey.config import garmin_info, exe_paths
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep

username_field = '//input[@name="username"]'
password_field = '//input[@name="password"]'
submit_button = '//button[@id]'
frame = '//iframe'
gen_url = "https://connect.garmin.com/signin/"
score_url = 'https://connect.garmin.com/modern/profile/433ae1d7-ba04-4209-bfa4-4814c426397d/scorecards'
source_data_location = Path(__file__).absolute().parent.parent.parent / 'data' / 'score_card_source.txt'

def enter_text_w_xpath(xpath, val):

    """
    Function Description: Enter text into an input field given the xpath.
    Function Parameters: xpath (String: The xpath of the element.),
        val (String: The value to be entered.)
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

    # Open session.
    driver = webdriver.Chrome(executable_path=exe_paths['sel_driver'])
    driver.get(gen_url)
    # Switch into frame.
    sleep(3)
    iframe = driver.find_element_by_xpath(frame)
    driver.switch_to.frame(iframe)
    # Enter credentials.
    enter_text_w_xpath(username_field, garmin_info['username'])
    enter_text_w_xpath(password_field, garmin_info['password'])
    driver.find_element_by_xpath(submit_button).click()

    if get_scorecard_ids:
        driver.get(score_url)                                  # Go to score cards.
        source = driver.page_source                            # Dump page into file for parsing. This will contain our scorecard ids.
        with open(source_data_location.absolute(), 'w+') as f:
            f.write(source)

    return driver

# print("Done")

driver = login_garmin()
url = 'https://connect.garmin.com/modern/proxy/gcs-golfcommunity/api/v2/scorecard/detail?scorecard-ids={}&include-next-previous-ids=true&user-locale=en'.format(155069236)
sleep(10)
driver.get(url)
print('PLZZZZ')
sleep(10)
print(driver.page_source)
sleep(5)