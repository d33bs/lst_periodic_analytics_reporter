"""
LST Periodic Analytics Reporter - Mediasite + Zoom + Google Drive Archiving
Intended for finding periodic stats on service usage.
Makes API requests, compiles data into files at specified location,
uploads data and files to Google Drive, then sends email to relevant parties.
Note: requires Mediasite report to already exist and various configurations/keys
to be provided in relevant sections.

pre-reqs: Python 3.x, requests, and google-api-python-client libraries
Last modified: Sept 2017
By: Dave Bunten

License: MIT - see license.txt
"""

import os
import sys
import logging
import argparse
import webbrowser
import html
import time
import datetime
import json
from string import Template
import integrations.mediasite.mediasite_reporter as mediasite_reporter
import integrations.zoom.zoom_reporter as zoom_reporter
import integrations.google.google_archiver as google_archiver

def run_periodic_analytics_reporter(config_file_path, logfile_path):
    """
    Function for gathering, communicating and archiving various data.

    arguments:
        config_file_path: file path to a JSON configuration file
        logfile_path: file path where logs will be stored locally
    """

    #load configuration data from JSON file
    config_file = open(config_file_path)
    config_data = json.load(config_file)

    #create report information using zoom
    logging.info("Gathering Zoom analytics")
    zoom_results = zoom_reporter.run_report(config_data["recurrence"],
        config_data["reporting_prefix"],
        config_data["export_destination"],
        config_data["zoom_account_list"]
        )

    #create report information using mediasite
    logging.info("Gathering Mediasite analytics")
    mediasite_results = mediasite_reporter.run_report(config_data["recurrence"],
        config_data["reporting_prefix"],
        config_data["export_destination"],
        config_data["mediasite_presentation_report_name"]
        )

    #gather date string for email
    if config_data["recurrence"] == "weekly":
        report_date_string = '{dt.month}/{dt.day}/{dt.year}'.format(dt = datetime.datetime.now())
    elif config_data["recurrence"] == "monthly":
        last_day_of_previous_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        report_date_string = last_day_of_previous_month.strftime("%m/%Y").lstrip("0")

    #create composite results dict for parsing results in email template
    all_results = mediasite_results.copy()
    all_results.update(zoom_results)
    all_results["email_report_date_string"] = report_date_string

    #archive results with google (includes spreadsheet additions and file backups)
    logging.info("Archiving results in Google")
    google_archiver.run_archiver(config_data["recurrence"],
        config_data["google_spreadsheet_id"],
        config_data["google_mediasite_archive_folder_id"],
        config_data["google_zoom_archive_folder_id"],
        config_data["google_spreadsheet_data_elements"],
        all_results
        )

    #create subject content using the current date and the template provided from the config file
    email_subj_template = Template(config_data["email_subj_template"])
    email_subj = email_subj_template.safe_substitute(email_report_date_string=all_results["email_report_date_string"])

    #create body content using the current data and the template provided from the config file
    email_body_template = Template("".join(config_data["email_body_template"]))
    email_body = email_body_template.safe_substitute(all_results)

    #send the email using gmail api
    logging.info("Sending report email")
    google_archiver.mailto(config_data["email_to"],
        config_data["email_reply_to"],
        config_data["email_cc"],
        email_subj,
        email_body
        )

    logging.info("Finished downloading data files and generating analytics email.")

    #upload the log to google drive as well once finished
    google_archiver.log_upload(logfile_path, config_data["google_log_folder_id"])

if __name__ == "__main__":
    """
    args:
        --file: json configuration file for setting details of report
    """
    #gather our runpath for future use with various files
    run_path = os.path.dirname(os.path.realpath(__file__))

    #log file datetime
    current_datetime_string = '{dt.month}-{dt.day}-{dt.year}_{dt.hour}-{dt.minute}-{dt.second}'.format(dt = datetime.datetime.now())
    logfile_path = run_path+'/logs/lst_periodic_reporter_'+current_datetime_string+'.log'

    #logger for log file
    logging_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging_datefmt = '%m/%d/%Y - %I:%M:%S %p'
    logging.basicConfig(filename=logfile_path,
        filemode='w',
        format=logging_format,
        datefmt=logging_datefmt,
        level=logging.INFO
        )

    #logger for console
    console = logging.StreamHandler()
    formatter = logging.Formatter(logging_format,
        datefmt=logging_datefmt)
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

    #parse arguments sent to program using ArgumentParser
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file',help='A JSON configuration file')
    args = parser.parse_args()

    #if our provided config file exists, start running analytics based on config
    if os.path.exists(args.file):
        run_periodic_analytics_reporter(args.file, logfile_path)
    else:
        #else we did not find the provided config file
        logging.error("Error: required configuration JSON file path not found.")
