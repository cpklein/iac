# iac
Scripts to deal with Integration as Code specification - **Integra.Sky**

## Postman → iac Converter
You can run this script locally. Just update the the following variables:

>examples_dir = 'subdirectory'
collection_file = 'your_collection.json'

This script was also meant to run as a proxied AWS Lambda Function.

METHOD: POST
**body**

    {
        "change" : {
            "include_response" : false,
            "remove_header" : [ 
                "Content-Type",
                "Accept"
            ],
            "change_variables" : {
                "server" : "my_server",
                "uk" : "",
                "baseUrl" : ""
            }
        },
        "collection" : {
        }
     }


### Collection Variables
All collection variables marked with double braces {{variable}} are converted to iac parameters. However, you may also **rename** or **remove** any existing variable using the **change_variables** object. You must specify any variable that you want to rename as the property and the value must contain the new name or "" (empty) if you want to remove it.


### Collections Response
Collections can store respective responses. They usually consume large amount of space and are currently not being used by the iac specification. You can remove the response from the iac file by specifying **include_response** as **false**.

### Path
The iac path is specified as a list with all the branches. This list may or may not be found on the original collection files. The script will generate the path list if not available on the original collection.
Variables specified on the path are marked with a ":" (colon) as the first character. These variables are also converted to iac parameters.

### Header
All collection header parameters are converted to iac prameters. You can remove any parameter by specifying its name on the **remove_header** list.

### Collection
The original collection must be specified in the parameter.


