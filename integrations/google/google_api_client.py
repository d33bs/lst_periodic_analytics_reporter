"""
Class for creating and using connections to Google Drive.
Special note: API access is presumed to be through a user and not a service acct.
Last modified: Dec 2016
By: Dave Bunten
"""

from __future__ import print_function
import httplib2
import os
import sys
import logging
import base64
from email.mime.text import MIMEText
from os.path import basename
from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.service_account import ServiceAccountCredentials

class gclient:
    def __init__(self, scopes, client_secret_file, application_name, delegate):
        """
        params:
            scopes: Google API scopes to use
            client_secret_file: filename of secret file downloaded from Google
            application_name: name of application utilizing the Google API
            delegate: for use with delegate accounts
        """
        # If modifying these scopes, delete your previously saved credentials
        # at ~/.credentials/
        self.flags = tools.argparser.parse_args([])
        self.scopes = scopes
        self.client_secret_file = client_secret_file
        self.application_name = application_name
        self.delegate = delegate

    def get_credentials(self):
        """
        Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        if getattr(sys, 'frozen', False):
            # frozen
            run_path = os.path.dirname(sys._MEIPASS)
        else:
            # unfrozen
            run_path = os.path.dirname(os.path.realpath(__file__))
        credential_path = run_path+"/"+'.googleapis_config.json'

        store = Storage(credential_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(run_path+"/"+self.client_secret_file, self.scopes)
            flow.params['access_type'] = 'offline'
            flow.approval_prompt = 'force'
            flow.user_agent = self.application_name
            # approval_prompt to 'force'
            if self.flags:
                credentials = tools.run_flow(flow, store, self.flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run_flow(flow, store)
        return credentials

    #for appending data to specified Google sheet by ID
    def sheet_insert_request(self, spreadsheet_id, insert_values, sheet_range='A:B'):
        """
        Inserts new row into Google spreadsheet with provided data.

        params:
            spreadsheet_id: ID of Google spreadsheet to insert values into
            insert_values: values to insert into Google spreadsheet
            sheet_range: range to use when inserting the values into Google spreadsheet
        """
        #Creates a Sheets API service object
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

        #create dummy range and var for data to insert
        append_data = {"values":[insert_values]}

        logging.info("Appending row of data to Google spreadsheet with id: "+spreadsheet_id)

        #send the data to be appended
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, valueInputOption="USER_ENTERED", range=sheet_range, body=append_data).execute()

    #for uploading files to Google Drive using source filepath and Google Drive folder ID
    def drive_upload_request(self, path_to_source_file, drive_folder_id):
        """
        Uploads file to Google Drive folder based on ID

        params:
            path_to_source_file: path to file which will be uploaded to Google Drive
            drive_folder_id: ID of Google Drive folder to upload file to
        """
        #Creates a Drive API service object
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        #create MediaFileUpload object for file to upload
        media_body = MediaFileUpload(path_to_source_file)

        #create meta data for file to upload
        body = {
            'name': basename(path_to_source_file),
            'parents':[drive_folder_id]
            }

        logging.info("Uploading "+basename(path_to_source_file)+" to Google Drive folder with id: "+drive_folder_id)

        #upload the file
        file = service.files().create(body=body, media_body=media_body).execute()

    #for sending content through email automatically (uses gmail)
    def gmail_send(self, mail_to, mail_reply_to, mail_cc, mail_subject, mail_content):
        """
        Function for sending Gmail email based on provided information in params

        params:
            mail_to: what email adddresses to send to delimited by commas
            mail_reply_to: who the email reply-to should be set as
            mail_cc: what emails adddresses to cc to delimited by commas
            mail_subject: email subject line
            mail_content: email body content
        """
        #Creates a Drive API service object
        credentials = self.get_credentials()
        #delegated_credentials = credentials.create_delegated(self.delegate)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        logging.info("Building email message")
        #Create a message for an email - uses html formatting for better spacing options
        message = MIMEText(mail_content, 'html')
        message['to'] = mail_to
        message['cc'] = mail_cc
        message['reply-to'] = mail_reply_to
        message['from'] = self.delegate
        message['subject'] = mail_subject
        message_content = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode('utf-8')}

        logging.info("Sending email message")
        #Send an email message.
        sent_message = (service.users().messages().send(userId=self.delegate, body=message_content).execute())
