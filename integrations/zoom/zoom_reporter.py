"""
LST Periodic Analytics Reporter - Zoom Reporter
Intended for finding periodic stats on Zoom service usage.
Note: uses zoom_web_api_client class to make requests
Last modified: July 2017
By: Dave Bunten
"""

import os
import sys
import logging
import json
import time
import math
import csv
import datetime
import integrations.zoom.zoom_web_api_client as zoom_web_api_client

#function for perfoming our write to CSV work based on provided list of rows and keys
def write_csv(download_filename, write_list, keys):
    """
    Function for writing CSV's based on a list of rows with various data

    arguments:
        download_filename: file path where resulting CSV will be stored
        write_list: list of dicts with keys
        keys: keys to write as columns for in each element of write_list
    """
    with open(download_filename, 'w', newline='') as fp:
        a = csv.DictWriter(fp, delimiter=',',fieldnames=keys, restval='',extrasaction='ignore')
        a.writeheader()
        a.writerows(write_list)
    logging.info("Finished creating Zoom stats file "+download_filename)

#function for
def zoom_daily_report(client, report_prefix, recurrence, zoom_results, export_destination):
    """
    Function for performing work to gather Zoom daily report information. Note
    that this is typically used when not interested in specific user reports and
    as such will gather different data - namely new user counts.

    arguments:
        client: zoom_web_api_client which is to be pre-built and provided to function
        report_prefix: used to specify the type of report (for ex. BBA, DLS, etc.)
        recurrence: the recurrence being used in the report used to set date ranges
        zoom_results: used for storing or appending to existing results
        export_destination: used for determining where to store exported csv w/data

    returns:
        zoom_results: dict with various summary data extracted from the Zoom API
    """

    #gather date strings for naming conventions
    start_date_string = time.strftime("%Y-%m-%d")
    start_date_file_string = time.strftime("%m-%d-%Y")

    #gather monthly information. Note: this is needed even if doing a weekly report
    #due to constraints with the Zoom API
    last_day_of_previous_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    previous_month_number = last_day_of_previous_month.strftime("%m").lstrip("0")
    current_month_number = datetime.date.today().strftime("%m").lstrip("0")
    year_number = last_day_of_previous_month.strftime("%Y")

    #if we're working with a weekly report, gather a list of the applicable dates
    if recurrence == "weekly":
        week_list = [(datetime.date.today() - datetime.timedelta(days=x)).strftime("%Y-%m-%d") for x in range(0, 7)]

    #list of keys we're interested in from the return data
    keys = ["date",
        "new_user",
        "meetings",
        "participants",
        "meeting_minutes"
        ]

    #list of keys we will need to find sums on
    sum_keys = ["new_user",
        "meetings",
        "participants",
        "meeting_minutes"
        ]

    def find_monthly_data(write_list, year_number, month_number, date_list=[]):
        """
        Function for performing requests to gather monthly Zoom data.

        arguments:
            write_list: for collecting rows of data for eventual report csv
            year_number: for specifying the year in the Zoom API request
            month_number: for specifying the month in the Zoom API request
            date_list: used for specifying a specific date range within month

        returns:
            write_list: a list of data for calculating report information
        """
        #run a daily report request using the year and month number provided
        result = client.do_request("report/getdailyreport", {"year":year_number,"month":month_number})
        result_json = json.loads(result)
        daily_results = result_json["dates"]

        #loop through dailyreport results for storing relevant content into write_list
        for user_data in daily_results:
            row = {}
            #for each date in date_list, gather information. Or if date_list is empty,
            #gather all data
            if any(str(user_data["date"]) in week_date for week_date in date_list) or len(date_list) == 0:
                #for each key, only keep those which are in keys list above
                for key,value in user_data.items():
                    if key in keys:
                        row[key] = value
                write_list.append(row)

        return write_list

    #final result data by row
    write_list = []

    #for weekly recurrence reports
    if recurrence == "weekly":
        write_list = find_monthly_data(write_list, year_number, current_month_number, week_list)
        #in the case that we need to gather weekly data from the previous month
        if len(write_list) < 7:
            write_list = find_monthly_data(write_list, year_number, previous_month_number, week_list)
    #for monthly recurrence reports
    elif recurrence == "monthly":
        write_list = find_monthly_data(write_list, year_number, previous_month_number)


    #initialize our col_sum dict for calculating sums of columns in csv
    col_sum = {key:0 for key in sum_keys}

    #determine sums row for write_list and the resulting report file/data
    for row_data in write_list:
        for key,value in row_data.items():

            #trigger for labeling the totals - will appear as cell 1 of final line in csv
            if key == "date":
                col_sum[key] = "totals"

            #for keys in the sum_keys list
            elif key in col_sum:
                col_sum[key] += int(value)

    #append the col_sums to the bottom of the write_list for csv
    write_list.append(col_sum)

    #create filename for csv
    download_filename = export_destination.rstrip('/')+'/zoom_report_'+\
        recurrence+'_'+report_prefix+'_'+start_date_file_string+'.csv'

    #write output as a csv
    write_csv(download_filename, write_list, keys)

    #store results and various other data in a dict which will be returned from function
    zoom_results["zoom_results_new_user"] = str(col_sum["new_user"])
    zoom_results["zoom_results_meetings"] = str(col_sum["meetings"])
    zoom_results["zoom_results_participants"] = str(col_sum["participants"])
    zoom_results["zoom_results_meeting_minutes"] = str(col_sum["meeting_minutes"])
    zoom_results["zoom_results_meeting_hours"] = str(math.ceil(int(zoom_results["zoom_results_meeting_minutes"])/60))
    zoom_results["zoom_results_csv_filepath"] = download_filename

    return zoom_results

def zoom_user_report(client, report_prefix, recurrence, zoom_results, export_destination, account_list):
    """
    Function for performing work to gather Zoom user report information. Note
    that this is typically used when not interested in more generic monthly reports
    and as such will gather different data.

    NOTE: that weekly reports can be run from any date and will gather data based
    #on 7 day period whereas monthly assumes the previous month from the current date

    arguments:
        client: zoom_web_api_client which is to be pre-built and provided to function
        report_prefix: used to specify the type of report (for ex. BBA, DLS, etc.)
        recurrence: the recurrence being used in the report used to set date ranges
        zoom_results: used for storing or appending to existing results
        export_destination: used for determining where to store exported csv w/data
        account_list: list of Zoom user accounts by email which we're interested in

    returns:
        zoom_results: dict with various summary data extracted from the Zoom API
    """
    #gather date strings for request based on recurrence
    if recurrence == "weekly":
        start_date = datetime.date.today()
        previous_date = datetime.date.today() - datetime.timedelta(days=7)
    elif recurrence == "monthly":
        start_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1))
        previous_date = start_date.replace(day=1)

    start_date_string = start_date.strftime("%Y-%m-%d")
    start_date_file_string = start_date.strftime("%m-%d-%Y")
    previous_date_string = previous_date.strftime("%Y-%m-%d")
    previous_date_file_string = previous_date.strftime("%m-%d-%Y")

    #list of keys we're interested in from the return data
    keys = ["user_id",
        "email",
        "meetings",
        "meeting_minutes",
        "participants"
        ]

    #list of keys we will need to find sums on
    sum_keys = ["meetings",
        "meeting_minutes",
        "participants"
        ]

    user_results = []
    user_result_number = 300
    page_count = 1

    #parse the result for the data we need using pages as necessary
    while user_result_number == 300:
        result = client.do_request("report/getaccountreport",
            {"from":previous_date_string,
                "to":start_date_string,
                "page_size":"300","page_number":str(page_count)
                }
        )
        result_json = json.loads(result)
        user_results.extend(result_json["users"])
        user_result_number = len(result_json["users"])
        page_count += 1

    logging.info("User object rows: "+str(len(user_results)))

    #final result data by row
    write_list = []

    #loop through the result users listing and filter by the account_list above
    for user_data in user_results:
        if any(sub in user_data["email"] for sub in account_list):
            row = {}
            #for each key, only keep those which are in keys list above
            for key,value in user_data.items():
                if key in keys:
                    row[key] = value
            write_list.append(row)

    #initialize our col_sum dict for calculating sums of columns in csv
    col_sum = {key:0 for key in sum_keys}

    #determine sums row for write_list and the resulting report file/data
    for row_data in write_list:
        for key,value in row_data.items():

            if key == "email":
                col_sum[key] = "totals"

            elif key in col_sum:
                    col_sum[key] += int(value)

    write_list.append(col_sum)

    #create filename for csv
    download_filename = export_destination.rstrip('/')+'/zoom_report_'+\
        recurrence+'_'+report_prefix+'_'+start_date_file_string+'.csv'

    #write output as a csv
    write_csv(download_filename, write_list, keys)

    logging.info("Storing data from report")

    zoom_results["zoom_results_meetings"] = str(col_sum["meetings"])
    zoom_results["zoom_results_participants"] = str(col_sum["participants"])
    zoom_results["zoom_results_meeting_minutes"] = str(col_sum["meeting_minutes"])
    zoom_results["zoom_results_meeting_hours"] = str(math.ceil(int(zoom_results["zoom_results_meeting_minutes"])/60))
    zoom_results["zoom_results_csv_filepath"] = download_filename

    return zoom_results

def run_report(recurrence, report_prefix, export_destination, account_list=[]):
    """
    Builds client for Zoom API and determines what type of report to run based
    on account_list count.

    arguments:
        recurrence: the recurrence being used in the report used to set date ranges
        report_prefix: used to specify the type of report (for ex. BBA, DLS, etc.)
        export_destination: used for determining where to store exported csv w/data
        account_list: list of Zoom user accounts by email which we're interested in

    returns:
        zoom_results: dict with various summary data extracted from the Zoom API
    """
    run_path = os.path.dirname(__file__)

    #open config file with api key/secret information
    api_config_file = open(run_path+"/"+".zoom_api_config")
    api_data = json.load(api_config_file)

    #create zoom client
    client = zoom_web_api_client.client(
        api_data["root_request_url"],
        api_data["api_key"],
        api_data["api_secret"],
        api_data["data_type"]
        )

    #construct results placeholders
    zoom_results = {"zoom_results_new_users":"",
        "zoom_results_meetings":"",
        "zoom_results_participants":"",
        "zoom_results_meeting_minutes":"",
        "zoom_results_meeting_hours":"",
        "zoom_results_csv_filepath":"",
        "zoom_results_email_content":""
        }

    #if provided an account list with accounts create user-based reports rather than
    #monthly reports
    if len(account_list) > 0:
        zoom_results = zoom_user_report(client, report_prefix, recurrence, zoom_results, export_destination, account_list)
    else:
        zoom_results = zoom_daily_report(client, report_prefix, recurrence, zoom_results, export_destination)

    return zoom_results
