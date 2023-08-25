# calabrio_py
An unofficial python client library for accessing the Calabrio API.

## Features
- Asynchronous and synchronous modes
- Methods for calling all Calabrio API endpoints
- Helper request objects for passing parameters to write operations
- Automatic serialization of request objects
- Response models for easy data access

For the details about each method, please refer documentation.md

# Quick Start
To use it:

Install 
```pip install calabrio-py```
Import the library
```
from calabrio_py.api import ApiClient, AsyncApiClient # choose either
```
Initialize the client with your API url and key
```
api_url = "https://yourcompany.teleopticloud.com/api"
api_key = "YOUR_API_KEY"
client = ApiClient(api_url, api_key)
```
Make a request to get all business units
```
business_units = client.get_all_business_units()
```
Make async requests by awaiting the client methods
```
client = AsyncApiClient(api_url, api_key)

business_units = await client.get_all_business_units()
print(business_units)
```

You can switch to sync mode by calling client.set_async(False)
See the class documentation for available methods

# Some things to note:

- Many write methods require a request object as input rather than just parameters
- Some read methods require the business unit ID and date as parameters
- Async requests require asyncio.run to execute
