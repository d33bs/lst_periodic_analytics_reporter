"""
LST Periodic Analytics Reporter - Mediasite Reporter
Intended for finding weekly stats on BBA Mediasite usage
Makes request for report to be generated using existing presentationanalytics items.
Next, must download both the xml and excel xml to the specified location.
Returns summary data, downloaded filepaths, and content for email
Last modified: July 2017
By: Dave Bunten
"""

import os
import logging
import json
import time
import datetime
import sys
import urllib.request
import xml.etree.ElementTree
import integrations.mediasite.mediasite_web_api_client as mediasite_web_api_client

def run_report(recurrence, report_prefix, export_destination, presentation_report_entry):
    """
    Primary function to run Mediasite report, download resulting data files, and
    return information pertaining to the results.

    params:
        recurrence: the period of the report, for ex. "weekly", "monthly"
        report_prefix: the prefix to use for the report, for ex. "bba", "dls"
        export_destination: local directory location for downloaded report files
        presentation_report_entry: presentation report name within Mediasite

    returns:
        mediasite_results: dict with various summary data extracted from the Mediasite API
    """

    run_path = os.path.dirname(os.path.realpath(__file__))

    #open config file with api key/secret information
    api_config_file = open(run_path+"/"+".mediasite_api_config")
    api_data = json.load(api_config_file)

    #create mediasite api client
    client = mediasite_web_api_client.client(
        api_data["base_url"],
        api_data["api_secret"],
        api_data["api_user"],
        api_data["api_pass"]
        )

    #initialize our final results dictionary
    mediasite_results = {"mediasite_results_total_time_watched":"",
        "mediasite_results_time_watched_hours":"",
        "mediasite_results_time_watched_miuntes":"",
        "mediasite_results_time_watched_seconds":"",
        "mediasite_results_number_presentations":"",
        "mediasite_results_watched_presentations":"",
        "mediasite_results_presentation_views":"",
        "mediasite_results_active_users":"",
        "mediasite_results_active_users_peak":"",
        "mediasite_results_excel_filepath":"",
        "mediasite_results_xml_filepath":"",
        "mediasite_results_email_content":""
        }

    #perform request
    #note: request includes odata attribute top to pull all information at once - otherwise the data will not include all results
    #http://www.odata.org/documentation/odata-version-3-0/odata-version-3-0-core-protocol/

    #determine presentation report ID
    logging.info("Finding ID of presentation report")
    presentation_report_result = client.do_request("get", "PresentationReports", "$top=1&$filter=Name eq '"+presentation_report_entry+"'", "")
    presentation_report_id = json.loads(presentation_report_result)["value"][0]["Id"]

    #execute the presentation report
    logging.info("Executing presentation report")
    presentation_report_execute = client.do_request("post","PresentationReports('"+presentation_report_id+"')/Execute", "", {})
    presentation_report_execute_json = json.loads(presentation_report_execute)

    #wait for the report to be generated
    wait_for_job_to_complete(presentation_report_execute_json["JobLink"], client)

    #gather date strings for request
    current_date_file_string = time.strftime("%m-%d-%Y")
    week_ago = datetime.date.today() - datetime.timedelta(days=7)
    week_ago_date_file_string = week_ago.strftime("%m-%d-%Y")

    #filenames and locations for the excel and xml files
    excel_filename = export_destination.rstrip('/')+"/mediasite_report_"+\
        recurrence+"_"+report_prefix+'_'+current_date_file_string+".excel.xml"
    xml_filename = export_destination.rstrip('/')+"/mediasite_report_"+\
        recurrence+"_"+report_prefix+'_'+current_date_file_string+".xml"

    #download excel (xml) version of data
    logging.info("Beginning Excel XML file generation for report")
    download_report_from_id(presentation_report_id, presentation_report_execute_json["ResultId"], "Excel", excel_filename, client)

    #download xml version of data
    logging.info("Beginning XML file generation for report")
    download_report_from_id(presentation_report_id, presentation_report_execute_json["ResultId"], "XML", xml_filename, client)

    #parse necessary data from xml file
    logging.info("Reading XML data from report")
    xml_data = xml.etree.ElementTree.parse(xml_filename)
    xml_root = xml_data.getroot()
    mediasite_results["mediasite_results_number_presentations"] = xml_root.find("ResultSummary").find("PresentationsAvailable").text
    mediasite_results["mediasite_results_total_time_watched"] = xml_root.find("ResultSummary").find("TotalTimeWatched").text
    mediasite_results["mediasite_results_watched_presentations"] = xml_root.find("ResultSummary").find("PresentationsWatched").text
    mediasite_results["mediasite_results_presentation_views"] = xml_root.find("ResultSummary").find("TotalViews").text
    mediasite_results["mediasite_results_active_users"] = xml_root.find("ResultSummary").find("TotalUsers").text
    mediasite_results["mediasite_results_active_users_peak"] = xml_root.find("ResultSummary").find("PeakConnections").text

    #organize our time for display
    #NOTE: hours are in days by default in xml file (not the case in excel xml file)
	#ex: <TotalTimeWatched>05:44:37</TotalTimeWatched>
    total_mediasite_time_watched_split = mediasite_results["mediasite_results_total_time_watched"].split(":")
    mediasite_results["mediasite_results_time_watched_minutes"] = total_mediasite_time_watched_split[1]
    mediasite_results["mediasite_results_time_watched_seconds"] = total_mediasite_time_watched_split[2]

    #hours cleanup (see above comment)
	#checking for decimal in days format first for special calculation
    if "." in total_mediasite_time_watched_split[0]:
        total_mediasite_time_watched_hours_split = total_mediasite_time_watched_split[0].split(".")
        mediasite_results["mediasite_results_time_watched_hours"] = str((int(total_mediasite_time_watched_hours_split[0])*24)+int(total_mediasite_time_watched_hours_split[1]))
    else:
        mediasite_results["mediasite_results_time_watched_hours"] = str((int(total_mediasite_time_watched_split[0])*24))

    mediasite_results["mediasite_results_excel_filepath"] = excel_filename
    mediasite_results["mediasite_results_xml_filepath"] = xml_filename

    #create strings for the email
    logging.info("Finished gathering Mediasite data, generating email content")

    return mediasite_results

def download_report_from_id(presentation_report_id, presentation_report_result_id, download_type, download_filename, client):
    """
    Function for downloading Mediasite reports using Mediasite API.

    arguments:
        presentation_report_id: Mediasite GUID for relevant report
        presentation_report_result_id: Mediasite GUID for relevant report result (data)
        download_type: type of file to request, for ex. "Excel" or "XML"
        download_filename: name of the resulting downloaded report data file
        client: pre-configured Mediasite API client to be provided for making download requests
    """
    #make request for report file to be generated
    presentation_report_execute_export = client.do_request("post", "PresentationReports('"+presentation_report_id+"')/Export", "", {"ResultId":presentation_report_result_id,"FileFormat":download_type})
    presentation_report_execute_export_json = json.loads(presentation_report_execute_export)

    #wait for the job to finish
    wait_for_job_to_complete(presentation_report_execute_export_json["JobLink"], client)
    logging.info("Attempting to download report from url: "+presentation_report_execute_export_json["DownloadLink"])

    #download the file as a stream
    with open(download_filename, 'wb') as handle:
        presentation_report_job_rsp = client.do_request("get stream",presentation_report_execute_export_json["DownloadLink"],"","")
        for block in presentation_report_job_rsp.iter_content(1024):
            handle.write(block)

    logging.info("Successfully downloaded "+download_filename)

def wait_for_job_to_complete(job_link_url, client):
    """
    Function for checking on and waiting for completion or error status of jobs in
    Mediasite system using Mediasite API.

    arguments:
        job_link_url: unique link to Mediasite job which can be used for gathering status
        client: pre-configured Mediasite API client to be provided for making requests
    """
    while 1:
        #gather information on the job status
        job_result = client.do_request("get job", job_link_url, "", "")
        job_result_status = json.loads(job_result)["Status"]

        #if successful we return
        if job_result_status == "Successful":
            logging.info("Job was successful")
            return

        #if the job fails or is canceled for some reason exit
        elif job_result_status == "Disabled" or job_result_status == "Failed" or job_result_status == "Cancelled":
            logging.error("Job "+presentation_report_execute_id+" did not complete successfully. Exiting.")
            sys.exit()

        #if the job is queued or working we wait for the job to finish or fail
        else:
            logging.info("Waiting for job to complete. Job status: "+job_result_status)
            time.sleep(5)
