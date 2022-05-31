"""
postman_converter.py
Caio Klein

This routine receives a Postamn collection json file and converts it to an
integra .iac file containing the modules specifications.
"""

import json
import os
import re
from urllib.parse import urlparse

#import boto3

# Auxiliary files to be used when running lically
# path to search the collection file
examples_dir = 'examples'
# Filename to convert
collection_file = 'cashu_collection.json'
#collection_file = 'vtex_postman_collection.json'
#collection_file = 'zoho_postman_collection.json'
#collection_file = 'anymarket_postman_collection.json'
#collection_file = 'ploomes.json'

# Global change specification to be used locally 
change = {
    "remove_header" : [ 
        "Content-Type",
        "Accept"
    ],
    "include_response" : False,
    "change_variables" : {
        "server" : "",
        "uk" : "",
        "baseUrl" : ""
    }
}

# Static header definition
connectors = {
    "name" : "Module Name",
    "description" : "Module Description",
    "type" : "REST",
    "settings" : {
        "authentication_type" : "Basic",
    }
}
# Default body to be used by .iac
default_body =  {
    "mode":"raw",
    "raw" : "<>ops_body</>",
    "options": {
        "raw": {
            "language": "json"
        }
    }
}

# When using via Lambda function, we expect the following body
"""
# Exemple of body inside the event
{
    "collection" : {},
    "change" : {
        "include_response" : False,
        "remove_header" : [
           "Accept"
        ]
        "change_variables" : {
            "server" : "",
            "uk" : "",
            "baseUrl" : ""
        }
    }
}
"""

def lambda_handler(event, context):
    global connectors
    global change
    res_msg = {}
    body_res = {}
    # Obtem body como dicionário
    req_body = json.loads(event['body'])
    
    if req_body.get('collection') == None:
        res_msg['statusCode'] = 400
        body_res['msg'] = "Collection Not Found"
        res_msg['body']= json.dumps(body_res)
        return (res_msg)
    #Update parameters with content that comes from request
    change = req_body.get('change', { })
    path = [] # List of branches describing the path
    operations = []
    build_operation (req_body["collection"]["item"], path, operations)
    connectors["operations"] = operations
    res_msg['statusCode'] = 200
    body_res['msg'] = "Success"
    body_res['modules'] = { 'connectors' : [ connectors ] }
    res_msg['body']= json.dumps(body_res, ensure_ascii=False)
    return (res_msg)
    

def process_parms(item):
    global change
    params = [] # list of new parameters in the form of a tuple ("parameter_name", "type")

    if type(item) is dict:
        # check all properties within dictionary
        for sub_item in item.keys():
            # if chield element is string we must process
            if type(item[sub_item]) is str:
                # search al occurences of parameters
                all_parms = re.findall(r'{{(.*?)}}', item[sub_item])
                # for each occurence check if it must be changed by config request
                for parm in all_parms:
                    if parm in change["change_variables"].keys():
                        # if not empty, we must change the name
                        if change["change_variables"][parm] != "":
                            new_string = "<>"+change["change_variables"][parm]+"</>"
                            params.append((change["change_variables"][parm], "string", ""))
                        else:
                            # if empty, we must clear the reference
                            new_string = ""
                    else:
                        # if not in change request we must just replace the marker
                        new_string = "<>" + parm + "</>"
                        params.append((parm, "string", ""))
                    # replace the original entry by the new one. 
                    # Dic is mutable so we change the original object
                    item[sub_item] = re.sub('{{'+parm+'}}', new_string, item[sub_item])
                    #print (sub_item,"\t", item[sub_item])
            else:
                # its not a string, so we assume its a list or dic. Send again to the function
                new_params = process_parms(item[sub_item])
                params.extend(new_params)
                
    else:
        if type(item) is list:
            # check all elements within list
            for i in range(len(item)):
                # if chield element is string we must process
                if type(item[i]) is str:
                    # search al occurences of parameters
                    all_parms = re.findall(r'{{(.*?)}}', item[i])
                    for parm in all_parms:
                        if parm in change["change_variables"].keys():
                            # if not empty, we must change the name
                            if change["change_variables"][parm] != "":
                                new_string = "<>"+change["change_variables"][parm]+"</>"
                                params.append((change["change_variables"][parm], "string", ""))
                            else:
                                # if empty, we must clear the reference
                                new_string = ""
                        else:
                            # if not in change request we must just replace the marker
                            new_string = "<>" + parm + "</>"
                            params.append((parm, "string", ""))
                        # replace the original entry by the new one. 
                        # Dic is mutable so we change the original object
                        item[i] = re.sub('{{'+parm+'}}', new_string, item[i])
                else:
                    new_params = process_parms(item[i])
                    params.extend(new_params)
    # return list of unique parameters
    return list(set(params))
            
def build_parms(parms):
    parameters = []
    for parm, p_type, sample in parms:
        parameter = { "name" : parm ,
                      "type" : p_type,
                      "description" : "",
                      "required" : False,
                      "sensitive" : False,
                      "sample" : sample}
        parameters.append(parameter)
    return parameters

def header_parms(parms):
    global change
    # We need to iterate on a copy, so we can remove items from the original
    iter_parms = parms.copy()
    parameters = []
    for parm in iter_parms:
        if parm["key"] not in change.get("remove_header", []):
            parameters.append((parm["key"], parm.get("type", "string"), parm["value"]))
            parm["value"] = "<>" + parm["key"] + "</>"
        else:
            parms.remove(parm)
    return parameters

def process_body(request):
    global default_body
    parameters = []
    # If body is raw (not urlencode or GraphQL) 
    if request["body"]["mode"] == "raw":
        # and not empty
        if request["body"]["raw"] != "":
            # Make it a parameter, extract raw
            parameters.append(("ops_body", "object", request["body"].pop("raw")))
            # Create a new parameterized body        
            request["body"] = default_body
    return parameters

def process_url(request):
    parms = []
    new_url = {}
    raw = ""
    # If url is str then we must break it
    if type(request["url"]) == str:
        raw = request["url"]
    # we found path hiden in the host then we must process the raw
    else:
        if request["url"].get("path") == None:
            raw = request["url"]["raw"]
    # If any of those conditions above
    if raw !="":
        url = urlparse(raw)
        # process path if any
        if url.path != "":
            path = url.path.split("/")
            # remove first element if empty
            if path[0] == "":
                del path[0]
            new_url["path"] = path
        # Process queries if any
        if url.query != "":
            new_url["query"] = []
            queries = url.query.split("&")
            for query in queries:
                try:
                    key, value = query.split("=", 1)
                    new_url["query"].append( {"key":key, "value":value})
                except:
                    print ("error query", query)
        # Update URL with new object
        request["url"] = new_url
    #Check for variables on the path
    for i in range(len(request['url']['path'])):
        # variables on path start with ":"
        if request['url']['path'][i][0] == ":":
            # Insert parameter in the list
            parms.append((request['url']['path'][i][1:], "string", ""))                
            # Remove ":" and add our markers
            request['url']['path'][i] = "<>" + request['url']['path'][i][1:] + "</>"
    return parms

def process_item(item, path):
    global change
    parms = []
    # Deal with RAW Body
    if item["request"].get("body"):
        parms.extend(process_body(item["request"]))

    # Deal with HEADERS
    if item["request"].get("header"):
        # process headers 
        parms.extend(header_parms(item["request"]["header"]))
        
    # Deal with URL
    if item["request"].get("url"):
        # process URL
        parms.extend(process_url(item["request"]))
    
    # remove response if not required
    # Removing here also evoid unexpected parameters configured on the responses
    if not change["include_response"]:
        item["response"] = []

    # Get all parameters in the form {{parm}} 
    parms.extend(process_parms(item))
        
    # Create the parameters section in the new definition
    item["parameters"] = build_parms(parms)
    # Update name with the full path
    item["name"] = ".".join(path) + "." + item["request"]["method"]
    # Move request description to root
    if item["request"].get("description"):
        item["description"] = item["request"].pop("description")
    return
        

def build_operation(item, path, operations):
    # Parse all objects inside de item
    for sub_item in item:
        path.append (sub_item["name"])            
        if "item" in sub_item.keys():
            build_operation(sub_item["item"], path, operations)
        else:
            process_item(sub_item, path)
            operations.append(sub_item)
        path.pop()
        

# For local test
if __name__ == "__main__":
    # Collection file must be specified 
    test_file = os.path.join(examples_dir, collection_file)
    with open(test_file, 'r') as mensagem:    
        data = mensagem.read()
    # parse file into dictionary
    collection = json.loads(data)
    
    #create the empty document
    path = [] # List of branches describing the path
    operations = []
    build_operation (collection["item"], path, operations)
    # just print the operations
    module = { "operations" : operations }
    json_out = json.dumps(module, indent = 3,ensure_ascii=False)
    print (json_out)
