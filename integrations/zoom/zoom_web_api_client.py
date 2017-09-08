"""
Class for creating connections to Zoom API
Last modified: Sept 2017
By: Dave Bunten
"""

import json
import requests
requests.packages.urllib3.disable_warnings()

class client:
	def __init__(self, root_request_url, key, secret, data_type):
		"""
		params:
			root_request_url: root URL to send API requests to
			key: Zoom API key to use when making requests
			secret: Zoom API secret to use when making requests
			data_type: data_type to use when Zoom API returns data, for ex. "XML","JSON"
		"""
		self.root_request_url = root_request_url
		self.key = key
		self.secret = secret
		self.data_type = data_type

	def do_request(self, resource, request_parameters):
		"""
		Performs API request based on parameter data

		params:
			resource: resource within the API to make requests on, for ex. "Meetings"
			request_parameters: request parameters to use when performing the request
		"""
		self.resource = resource
		self.request_parameters = request_parameters

        #create URL based on what we're requesting
		url = self.root_request_url + self.resource

        # Header values required for Zoom API request
		values = {
			"api_key":self.key,
			"api_secret":self.secret,
			"data_type":self.data_type
			}

        #add the request params to the values dictionary to be sent in request
		values.update(self.request_parameters)

        #attempt to make request and return results if successful
        #else return the error
		try:
			rsp = requests.post(url, data=values, verify=False)
			content = rsp.text
			return content
		except HTTPError as e:
			return e.response.status_code
