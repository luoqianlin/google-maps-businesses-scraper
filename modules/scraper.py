from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from modules.helpers import *
from modules.const.settings import SETTINGS
from modules.const.colors import fore

import time
import json
import xlsxwriter


def scrape(args):
    '''
    Scrapes the results and puts them in the excel spreadsheet.

    Parameters:
            args (object): CLI arguments
    '''
    if args.pages is not None:
        SETTINGS["PAGE_DEPTH"] = args.pages
    SETTINGS["BASE_QUERY"] = args.query
    SETTINGS["PLACES"] = args.places.split(',')

    # Created driver and wait
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    # Set main box class name
    BOX_CLASS = "CUwbzc-content"

    # Initialize workbook / worksheet
    workbook = xlsxwriter.Workbook('ScrapedData_GoogleMaps.xlsx')
    worksheet = workbook.add_worksheet()

    # Headers and data
    data = {
        "name": "",
        "phone": "",
        "address": "",
        "website": "",
        "email": ""
    }
    headers = generate_headers(args, data)
    print_table_headers(worksheet, headers)

    # Start from second row in xlsx, as first one is reserved for headers
    row = 1

    # Remember scraped addresses to skip duplicates
    addresses_scraped = {}

    start_time = time.time()

    for place in SETTINGS["PLACES"]:
        # Go to the index page
        driver.get(SETTINGS["MAPS_INDEX"])

        # Build the query string
        query = "{0} {1}".format(SETTINGS["BASE_QUERY"], place)
        print(f"{fore.GREEN}Moving on to {place}{fore.RESET}")

        # Fill in the input and press enter to search
        q_input = driver.find_element_by_name("q")
        q_input.send_keys(query, Keys.ENTER)

        # Wait for the results page to load. If no results load in 10 seconds, continue to next place
        try:
            w = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, BOX_CLASS))
            )
        except:
            continue

        # Loop through pages and results
        for _ in range(0, SETTINGS["PAGE_DEPTH"]):
            # Get all the results boxes
            boxes = driver.find_elements_by_class_name(BOX_CLASS)

            # Loop through all boxes and get the info from it and store into an excel
            for box in boxes:
                # Just get the values, add only after we determine this is not a duplicate (or duplicates should not be skiped)
                name = box.find_element_by_class_name("qBF1Pd").find_element_by_xpath(".//span").text
                print('name', name)
                address_and_phone = box.find_elements_by_xpath("./div[@class='ZY2y6b-RWgCYc']")[1]
                try:
                    address = address_and_phone.find_element_by_xpath("./div[1]/span[2]/jsl/span[2]").text
                except:
                    address = ''
                scraped = address in addresses_scraped

                if scraped and args.skip_duplicate_addresses:
                    print(f"{fore.WARNING}Skipping {name} as duplicate by address{fore.RESET}")
                else:
                    if len(address_and_phone.find_elements_by_xpath('.//div')) > 1:
                        phone = address_and_phone.find_element_by_xpath("./div[2]/span[last()]/jsl/span[2]").text
                    else:
                        phone = ''
                    print('address:', address)
                    print('phone:', phone)

                    if scraped:
                        addresses_scraped[address] += 1
                        print(
                            f"{fore.WARNING}Currently scraping on{fore.RESET}: {name}, for the {addresses_scraped[address]}. time")
                    else:
                        addresses_scraped[address] = 1
                        print(f"{fore.GREEN}Currently scraping on{fore.RESET}: {name}")

                    # Only if user wants to get the URL to, get it
                    if args.scrape_website:
                        url = box.find_element_by_class_name(
                            "section-result-action-icon-container").find_element_by_xpath("./..").get_attribute("href")
                        website, email = get_website_data(url)
                        if website is not None:
                            data["website"] = website
                        if email is not None:
                            data["email"] = ','.join(email)

                    data["name"] = name
                    data["address"] = address
                    data["phone"] = phone

                    # If additional output is requested
                    if args.verbose:
                        print(json.dumps(data, indent=1))

                    write_data_row(worksheet, data, row)
                    row += 1
            # ppdPk-Ej1Yeb-LgbsSe-tJiF1e
            # Go to next page                                
            next_page_link = driver.find_element_by_id("ppdPk-Ej1Yeb-LgbsSe-tJiF1e")

            try:
                next_page_link.click()
            except WebDriverException:
                print(f"{fore.WARNING}No more pages for this search. Advancing to next one.{fore.RESET}")
                break

            # Wait for the next page to load
            time.sleep(5)
        print("-------------------")

    workbook.close()
    driver.close()

    end_time = time.time()
    elapsed = round(end_time - start_time, 2)
    print(f"{fore.GREEN}Done. Time it took was {elapsed}s{fore.RESET}")
