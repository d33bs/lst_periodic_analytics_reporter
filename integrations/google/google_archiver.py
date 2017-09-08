"""
LST Periodic Analytics Reporter - Google Archiver
Intended for sending data to Google spreadsheet and uploading data exported
from mediasite_reporter and zoom_reporter.
Last modified: July 2017
By: Dave Bunten
"""

import os
import ntpath
import sys
import logging
import time
import datetime
import json
import integrations.google.google_api_client as google_api_client

def run_archiver(recurrence, google_spreadsheet_id, google_mediasite_archive_folder_id, google_zoom_archive_folder_id, google_spreadsheet_data_elements, all_results ):
    """
    Primary function to store data in central spreadsheet and archive data result files
    on Google Drive.

    params:
        recurrence: the period of the report, for ex. "weekly", "monthly"
        google_spreadsheet_id: ID of Google Docs spreadsheet to store data in
        google_mediasite_archive_folder_id: ID of Google Drive folder to store Mediasite result files
        google_zoom_archive_folder_id: ID of Google Drive folder to store Zoom result files
        google_spreadsheet_data_elements: data to store from various reports
    """
    run_path = os.path.dirname(os.path.realpath(__file__))

    #open config file with api key/secret information
    client_config_file = open(run_path+"/"+".google_client_config")
    client_data = json.load(client_config_file)

    #create Google api client
    client = google_api_client.gclient(
        client_data["auth_scope"],
        client_data["auth_secret"],
        client_data["app_name"],
        client_data["delegate"]
        )

    #gather date labeling for the reports based on the recurrence
    if recurrence == "weekly":
        current_date_string = '{dt.month}/{dt.day}/{dt.year}'.format(dt = datetime.datetime.now())
        week_ago_date_string = '{week_ago.month}/{week_ago.day}/{week_ago.year}'.format(week_ago = datetime.date.today() - datetime.timedelta(days=7))
        date_string = week_ago_date_string+"-"+current_date_string
    elif recurrence == "monthly":
        last_day_of_previous_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        last_month_abbr = last_day_of_previous_month.strftime("%b")
        last_month_year = last_day_of_previous_month.strftime("%Y")
        date_string = last_month_abbr+" "+last_month_year

    #prepend the date string to the beginning of the google_spreadsheet_data_elements
    spreadsheet_data = [date_string]
    for elem in google_spreadsheet_data_elements:
        if elem != "":
            spreadsheet_data.append(all_results[elem])
        else:
            spreadsheet_data.append("")

    #append data to specified Google spreadsheet
    logging.info("Sending data to analytics spreadsheet")
    client.sheet_insert_request(google_spreadsheet_id, spreadsheet_data)

    #upload exported data files to Google Drive
    logging.info("Uploading data export files to Google Drive")
    client.drive_upload_request(all_results["mediasite_results_excel_filepath"],google_mediasite_archive_folder_id)
    client.drive_upload_request(all_results["mediasite_results_xml_filepath"],google_mediasite_archive_folder_id)
    client.drive_upload_request(all_results["zoom_results_csv_filepath"],google_zoom_archive_folder_id)

def mailto(mail_to, mail_reply_to, mail_cc, mail_subject, mail_content):
    """
    Function for sending Gmail email based on provided information in params

    params:
        mail_to: what email adddresses to send to delimited by commas
        mail_reply_to: who the email reply-to should be set as
        mail_cc: what emails adddresses to cc to delimited by commas
        mail_subject: email subject line
        mail_content: email body content
    """
    run_path = os.path.dirname(os.path.realpath(__file__))

    #open config file with api key/secret information
    client_config_file = open(run_path+"/"+".google_client_config")
    client_data = json.load(client_config_file)

    #create Google api client
    client = google_api_client.gclient(
        client_data["auth_scope"],
        client_data["auth_secret"],
        client_data["app_name"],
        client_data["delegate"]
        )

    client.gmail_send(mail_to, mail_reply_to, mail_cc, mail_subject, mail_content)

def log_upload(log_filepath, google_log_folder_id):
    """
    Function for uploading log file to Google Drive folder

    params:
        log_filepath: filepath for the log to be uploaded
        google_log_folder_id: ID of Google Drive folder where log to be uploaded
    """
    run_path = os.path.dirname(os.path.realpath(__file__))

    #open config file with api key/secret information
    client_config_file = open(run_path+"/"+".google_client_config")
    client_data = json.load(client_config_file)

    #create Google api client
    client = google_api_client.gclient(
        client_data["auth_scope"],
        client_data["auth_secret"],
        client_data["app_name"],
        client_data["delegate"]
        )

    #perform the upload of the file
    logging.info("Uploading log file to Google Drive")
    client.drive_upload_request(log_filepath, google_log_folder_id)
