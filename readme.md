# LST Periodic Analytics Reporter

This application gathers data from various sources (for ex. Mediasite and Zoom) and sends it to a centralized Google Drive location for analysis and historical tracking.

## Prerequisites and Documentation

Before you get started, make sure to install or create the following prerequisites:

* Python 3.x: [https://www.python.org/downloads/](https://www.python.org/downloads/)
* Python Requests Library (non-native library used for HTTP requests): [http://docs.python-requests.org/en/master/](http://docs.python-requests.org/en/master/)
* Google API Python Library: [https://developers.google.com/api-client-library/python/start/installation](https://developers.google.com/api-client-library/python/start/installation)
* Enable Zoom API key: [https://zoom.us/developer/api/credential](https://zoom.us/developer/api/credential)
* A Mediasite user with operations "API Access" and "Manage Auth Tickets" (configurable within the Mediasite Management Portal)
* A Mediasite API key: [https://&lt;your-hostname&gt;/mediasite/api/Docs/ApiKeyRegistration.aspx](https://&lt;your-hostname&gt;/mediasite/api/Docs/ApiKeyRegistration.aspx)

Zoom API documentation can be found at the following URL: [https://zoom.github.io/api/](https://zoom.github.io/api/)

Mediasite API documentation can be found at the following URL (change the bracketed area to your site-specific base domain name): [http://&lt;your-hostname&gt;/mediasite/api/v1/$metadata](http://&lt;your-hostname&gt;/mediasite/api/v1/$metadata)

Also worth noting, as stated in the documentation, the Mediasite API makes heavy use of the ODATA standard for some requests (including the demo performed within this repo). For more docuemntation on this standard reference the following URL: [http://www.odata.org/documentation/odata-version-3-0/url-conventions/#requestingdata](http://www.odata.org/documentation/odata-version-3-0/url-conventions/#requestingdata)

## Usage

1. Ensure prerequisites outlined above are completed.
1. Fill in necessary information within config/example_config.json and rename to project specifics
1. Fill in necessary &lt;bracketed&gt; areas in .zoom_api_config_sample specific to your account
1. Fill in necessary &lt;bracketed&gt; areas in .mediasite_api_config_sample specific to your account
1. Fill in necessary &lt;bracketed&gt; areas in .google_client_config_sample specific to your account
1. Copy or rename downloaded secret file from Google Developer API Console to .google_api_secret_sample
1. Remove the text "_sample" from all config files
1. Run main.py with --file set to your configured JSON file from step 2 with Python 3.x

### Sample Usage

    C:\Users\sgtpepper>python C:\lst_periodic_reporter\main.py --file C:\lst_periodic_reporter\example_config.json
    09/06/2017 - 03:43:15 PM - INFO - Gathering Zoom analytics
    09/06/2017 - 03:43:15 PM - INFO - Starting new HTTPS connection (1): api.zoom.us
    09/06/2017 - 03:43:16 PM - INFO - Starting new HTTPS connection (1): api.zoom.us
    09/06/2017 - 03:43:17 PM - INFO - User object rows: 391
    09/06/2017 - 03:43:17 PM - INFO - Finished creating Zoom stats file C:\example_zoom_data.csv
    09/06/2017 - 03:43:17 PM - INFO - Storing data from report
    09/06/2017 - 03:43:17 PM - INFO - Gathering Mediasite analytics
    09/06/2017 - 03:43:17 PM - INFO - Finding ID of presentation report
    ...
    
## License

MIT - See license.txt
