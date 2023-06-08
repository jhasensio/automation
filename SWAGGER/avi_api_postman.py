import json
import os
import glob
import operator
from datetime import datetime
class avi_postman(object):
    
    def __init__(self, file_dir=None,json_file = None):
        if file_dir:
            self.file_dir = file_dir
            if os.path.exists(self.file_dir) and os.path.isdir(self.file_dir):
                pass
            else:
                print(f"{self.file_dir} either doesn't exist or is not a folder")
                exit(1)
        if json_file:
            self.json_file = json_file
            if os.path.exists(self.json_file) and os.path.isfile(self.json_file):
                f1 = open(self.json_file,"r")
                self.json_data = json.load(f1)
                f1.close()
                self.cond1 = "header"
                self.cond2 = "query"
                self.cond3 = "auth"
                self.count_cond1 = 0
                self.count_cond2 = 0
                self.count_cond3 = 0
            else:
                print(f"{self.json_file} either doesn't exist or is not a file")    
                exit(1)
                    
    def generate_report(self):
        """
        This function analyzes Avi swagger json files.
        If there is any duplicated API URI among those json files, it will generate a report file for all the duplicated API URI.
        If there is no duplicated API, the it will combined all API Pathes from those swagger json files, and generate one big json file for importing to Postman
        """
        self.version = self.file_dir.split("/")[-1]
        API_report = {"version":self.version, "report":[]}

            
        #only process .JSON files in folder.    
        api_jsonfile_List = sorted(glob.glob(os.path.join(self.file_dir, '*.json')) )  
            
        for filename in api_jsonfile_List: 
            # exclude avi_global_spec which will cause duplicated api path
            if filename != self.file_dir + "/avi_global_spec.json" and filename != self.file_dir + "/package.json" :
                with open(filename, encoding='utf-8', mode='r') as currentFile:
                    single_report = {"name":"","path":[]}
                    data=json.load(currentFile)
                    for k in data.keys():
                        if k.lower() == "paths":
                            single_report["name"] = data["info"]["title"]
                            single_report["path"] = list(data[k].keys())
                            API_report["report"].append(single_report)
                        
                    currentFile.close()
                

        # dump all api to the list in order to find out duplicated api path
        plain_path_list = []

        for item in API_report["report"]:
            plain_path_list.extend(item["path"])


        path_set = set()
        duplicated_path = set()
        for item in plain_path_list:
            if item not in path_set:
                path_set.add(item)
            elif item not in duplicated_path:
                duplicated_path.add(item)
                
        if len(duplicated_path) > 0:
            print(f"Duplicated API path found! A report file has been created! Please solve that issue and re-run the script!")
            duplicated_path_report = {"version":self.version, "report":[]}
            for value in duplicated_path:
                for item in API_report["report"]:
                    single_report = {"name":"","path":[]}
                    if value in item["path"]:
                        single_report["path"] = value
                        single_report["name"] = item["name"]
                        duplicated_path_report["report"].append(single_report)                     
                    
            duplicated_path_file_name = "Avi_" + self.version + "_duplicated_api_path_report.json"
            duplicated_report_f1 = open(duplicated_path_file_name, "w")
            duplicated_report_f1.write(json.dumps(duplicated_path_report, indent=4))   
                    
        else:
            print("No duplicated api path found")   
            print("Combining all json file ")   
            avi_postman = {
                "swagger": "2.0",
                "info": {
                    "version": self.version,
                    "title": f"Avi_{self.version}",
                    "contact": {
                        "name": "Avi Networks Inc.",
                        "url": "https://avinetworks.com/contact-us",
                        "email": "support@avinetworks.com"
                    },
                    "description": ""
                },
                "securityDefinitions": {
                    # "basicAuth": {
                    #     "type": "basic",
                    #     "description": "basic authentication"
                    # }
                },
                "basePath": "/api",
                "paths": {
                },
                "definitions": {
                },
                "_comment": [
                    "Copyright 2023 VMware, Inc.",
                    "SPDX-License-Identifier: Apache License 2.0"
                ]
            }
            
            for filename in api_jsonfile_List:
                # exclude avi_global_spec which will cause duplicated api path
                if filename != self.file_dir + "/avi_global_spec.json" and filename != self.file_dir + "/package.json" :
                    with open(filename, encoding='utf-8', mode='r') as currentFile:
                        data=json.load(currentFile)
                        for k in data.keys():
                            if k.lower() == "paths":
                                avi_postman["paths"].update(data[k])
                            if k.lower() == "definitions":
                                avi_postman["definitions"].update(data[k])
                            
                    currentFile.close()
                    
            joined_json_file_name = "Avi_" + self.version + "_api_json_joined.json"
            joined_f1 = open(joined_json_file_name, "w")
            joined_f1.write(json.dumps(avi_postman, indent=4))     

                
        all_api_file_name = "Avi_" + self.version + "_api_path_report.json"
        report_f1 = open(all_api_file_name, "w")
        report_f1.write(json.dumps(API_report, indent=4))        
    
    def ModifyHeader(self,headers:list):
        """
        This function is to:
        a. set the API header values:
        b. "X-Avi-Tenant-UUID" headers non-checked in postman by default
        """
        header_list = []
        for header in headers:
            # Set those four  X-Avi-* headers to pre-defined variables 
            if header['key'] in ["X-Avi-Tenant","X-Avi-Tenant-UUID","X-CSRFToken", "X-Avi-Version"]:
                header["value"] = "{{" + header['key'] + "}}"
            # Uncheck tenant UUID header
            if header['key'] in ["X-Avi-Tenant-UUID"]:
                header['disabled']=True
            # retrieve all headers   
            if header['key'] not in header_list:
                header_list.append(header['key'])
        
        # add 'Referer' head if not there
        # This head is required for POST/PATCH operations
        if 'Referer' not in header_list:
            head_referer=    {
                "description": "Referer header",
                "key": "Referer",
                "value": "{{Url}}"
            }
        headers.append(head_referer)
        
    def DisableQueryOptions(self,query):
        """
        This function unchecks all postman query options by default to make it easier to use.
        """
        for option in query:
            if isinstance(option, dict):
                option["disabled"]=True
                

    def ModifyJson(self,data):
        """
        This function iterates through Postman collection and do all the header/query operation, as well as removing \
        basic authentication method for each API
        """
        for item in data.copy().keys():
            if item == self.cond1:

                self.count_cond1+=1
                # do what we need
                self.ModifyHeader(data[item])
            
            elif item == self.cond2:

                self.count_cond2+=1
                self.DisableQueryOptions(data[item])
            
            # remove auth method for all api calls
            elif item == self.cond3:

                self.count_cond3+=1
                data.pop(self.cond3)
                
            elif isinstance(data[item],list):
                for element in data[item]:
                    if isinstance(element, dict):
                        self.ModifyJson(element)
            elif isinstance(data[item], dict):
                self.ModifyJson(data[item])
                

    def AddLogInOutRequest(self):
        loginout = {
            "name": "0-Login/out",
            "item": [
                {
                    "name": "Login",
                    "event": [
                        {
                            "listen": "test",
                            "script": {
                                "exec": [
                                    "var token1 = postman.getResponseCookie(\"csrftoken\").value;",
                                    "var token2 = token1.replace(\"<br/>\",\"\");",
                                    "pm.collectionVariables.set(\"X-CSRFToken\", token2);"
                                ],
                                "type": "text/javascript"
                            }
                        }
                    ],
                    "request": {
                        "method": "POST",
                        "header": [],
                        "body": {
                            "mode": "formdata",
                            "formdata": [
                                {
                                    "key": "username",
                                    "value": "admin",
                                    "type": "text"
                                },
                                {
                                    "key": "password",
                                    "value": "xxxxxx",
                                    "type": "text"
                                }
                            ]
                        },
                        "url": {
                            "raw": "{{Url}}/login",
                            "host": [
                                "{{Url}}"
                            ],
                            "path": [
                                "login"
                            ]
                        }
                    },
                    "response": []
                },
                {
                    "name": "Logout",
                    "request": {
                        "method": "POST",
                        "header": [
                            {
                                "key": "X-CSRFToken",
                                "value": "{{X-CSRFToken}}",
                                "type": "default"
                            },
                            {
                                "key": "Referer",
                                "value": "{{Url}}",
                                "type": "default"
                            }
                        ],
                        "body": {
                            "mode": "formdata",
                            "formdata": []
                        },
                        "url": {
                            "raw": "{{Url}}/logout",
                            "host": [
                                "{{Url}}"
                            ],
                            "path": [
                                "logout"
                            ]
                        }
                    },
                    "response": []
                }
            ]
        }
        self.json_data['item'].append(loginout)
    
    def AddAnalyticsRequest(self):
        """
        Postman will consolidate anomaly, healthscore and metrics under analytics as they all under the analytics path
        This function adds logs API call to analytics
        """

        logs =   {
            "name": "logs",
            "item": [
                {
                    "name": "Logs API",
                    "request": {
                        "method": "GET",
                        "header": [
                            {
                                "description": "Avi Tenant Header",
                                "key": "X-Avi-Tenant",
                                "value": "{{X-Avi-Tenant}}"
                            },
                            {
                                "description": "Avi Tenant Header UUID",
                                "key": "X-Avi-Tenant-UUID",
                                "value": "{{X-Avi-Tenant-UUID}}",
                                "disabled": True
                            },
                            {
                                "description": "Avi Controller may send back CSRF token in the response cookies. The caller should update the request headers with this token else controller will reject requests.",
                                "key": "X-CSRFToken",
                                "value": "{{X-CSRFToken}}"
                            },
                            {
                                "description": "(Required) The caller is required to set Avi Version Header to the expected version of configuration. The response from the controller will provide and accept data according to the specified version. The controller will reject POST and PUT requests where the data is not compatible with the specified version.",
                                "key": "X-Avi-Version",
                                "value": "{{X-Avi-Version}}"
                            },
                            {
                                "description": "Referer header",
                                "key": "Referer",
                                "value": "{{Url}}"
                            }
                        ],
                        "url": {
                            "raw": "{{baseUrl}}/analytics/logs",
                            "host": [
                                "{{baseUrl}}"
                            ],
                            "path": [
                                "analytics",
                                "logs"
                            ],
                            "query": [
                                {
                                    "key": "type",
                                    "value": "",
                                    "description": "OPTIONAL; Type of Logs Requested; 0: Connection Logs, 1: Application Logs, 2: Event Logs; DEFAULT=Automatically detected based on the VS's app profile\n",
                                    "disabled": True
                                },
                                {
                                    "key": "virtualservice",
                                    "value": "",
                                    "description": "REQUIRED; Specify VS ID for scoping the results\n",
                                    "disabled": True
                                },
                                {
                                    "key": "start",
                                    "value": "",
                                    "description": "OPTIONAL; start time stamp in ISO8601 format; DEFAULT=zero\n",
                                    "disabled": True
                                },
                                {
                                    "key": "end",
                                    "value": "",
                                    "description": "OPTIONAL; end time stamp in ISO8601 format; DEFAULT=current time\n",
                                    "disabled": True
                                },
                                {
                                    "key": "duration",
                                    "value": "",
                                    "description": "OPTIONAL; if start time is not specified (or set to zero), this field, specified in seconds, determines the duration from end for which logs are returned. DEFAULT=zero(no limit)\n",
                                    "disabled": True
                                },
                                {
                                    "key": "page_size",
                                    "value": "",
                                    "description": "OPTIONAL; maximum number of records to return; DEFAULT=10\n",
                                    "disabled": True
                                },
                                {
                                    "key": "adf",
                                    "value": "",
                                    "description": "OPTIONAL; search logs matching Avi Defined (Significant) Filters; DEFAULT=True\n",
                                    "disabled": True
                                },
                                {
                                    "key": "udf",
                                    "value": "",
                                    "description": "OPTIONAL; search through logs meeting User Defined Filters; DEFAULT=False\n",
                                    "disabled": True
                                },
                                {
                                    "key": "nf",
                                    "value": "",
                                    "description": "OPTIONAL; search through the rest of the logs (i.e., logs that match neither ADF nor UDF); DEFAULT=False\n",
                                    "disabled": True
                                },
                                {
                                    "key": "format",
                                    "value": "",
                                    "description": "OPTIONAL: choose a format for the data; Options={'json','csv','txt'}; DEFAULT='json'\n",
                                    "disabled": True
                                },
                                {
                                    "key": "page",
                                    "value": "",
                                    "description": "OPTIONAL; For pagination support; DEFAULT=1\n",
                                    "disabled": True
                                },
                                {
                                    "key": "filter",
                                    "value": "",
                                    "description": "OPTIONAL; Format: OPERATOR(field,value); Can be specified multiple times; DEFAULT=None See more information about filters here.\n",
                                    "disabled": True
                                },
                                {
                                    "key": "cols",
                                    "value": "",
                                    "description": "OPTIONAL; A comma separated list of fields to include in the results; When groupby is specified, sum/avg/max/min functions can be used with field names (e.g., sum(tx_bytes) in L4 case, or sum(response_length+request_length) in L7); you can order on the first custom column by specifying orderby=col0; DEFAULT=All when groupby is not specified and is sum(1) otherwise\n",
                                    "disabled": True
                                },
                                {
                                    "key": "groupby",
                                    "value": "",
                                    "description": "OPTIONAL; Specify a field name to group the results on; DEFAULT=None\n",
                                    "disabled": True
                                },
                                {
                                    "key": "orderby",
                                    "value": "",
                                    "description": "OPTIONAL; Specify a field name to sort the results on; Prepend with '-' to sort in reverse order; DEFAULT=-report_timestamp when groupby is not specified and descending order on count of items in each group (-count) when groupby is specified\n",
                                    "disabled": True
                                },
                                {
                                    "key": "step",
                                    "value": "",
                                    "description": "OPTIONAL; Specify step values for each groupby fieldresults; This outputs a JSON object, by default, with counts of logs that fall in each step, along with the timestamp of the end of the step; TBD: Summarization functions for other columns DEFAULT=0\n",
                                    "disabled": True
                                },
                                {
                                    "key": "expstep",
                                    "value": "",
                                    "description": "OPTIONAL; If set to true, then instead of default linear increases by 'step', we use an exponentially increasing steps; e.g., if step=2 and expstep=True, then the intervals in the responses will be of form: 0-1, 1-2, 2-4, 4-8, 8-16, and so on.; DEFAULT=False\n",
                                    "disabled": True
                                },
                                {
                                    "key": "timeout",
                                    "value": "",
                                    "description": "OPTIONAL; Specify the timeout (in seconds) for this query; DEFAULT=5\n",
                                    "disabled": True
                                },
                                {
                                    "key": "download",
                                    "value": "",
                                    "description": "OPTIONAL; Boolean; If set to true, then the results in the requested format will be downloaded as file. Also, the defaults for other options will be set as follows: format is set to CSV; timeout is set to 10 seconds; page is set to 1; page_size is set to 10000; DEFAULT=False\n",
                                    "disabled": True
                                },
                                {
                                    "key": "debug",
                                    "value": "",
                                    "description": "OPTIONAL; Boolean; If set to true, then we include extra debugging info in the responses; DEFAULT=False\n",
                                    "disabled": True
                                },
                                {
                                    "key": "js_compat",
                                    "value": "",
                                    "description": "OPTIONAL: Boolean; If set to true, then we will convert uint64 numbers to string in log query response.",
                                    "disabled": True
                                }
                            ]
                        }
                    },
                    "response": []
                }
            ]
        }

        for api_item in self.json_data['item'].copy():
            if api_item['name'] == "analytics":
                api_item["item"].append(logs)               
                
    def SetVariables(self):
        version= input("Please specifiy the API version (example: 22.1.3): ")
        variable_list = [
            {
                "key": "baseUrl",
                "value": "https://x.x.x.x/api",
                "type": "string"
            },
            {
                "key": "Url",
                "value": "https://x.x.x.x",
                "type": "default"
            },
            {
                "key": "X-Avi-Tenant",
                "value": "*",
                "type": "default"
            },
            {
                "key": "X-Avi-Tenant-UUID",
                "value": "",
                "type": "default"
            },
            {
                "key": "X-CSRFToken",
                "value": "",
                "type": "default"
            },
            {
                "key": "X-Avi-Version",
                "value": version,
                "type": "default"
            }
        ]
        self.json_data["variable"]= variable_list
        return version
    
if __name__ == "__main__":
    print(10*"#", "Please Choose option 1 or 2",10*"#")
    print("[1. Generate report]")
    print("[2. Modify Json file]")
    print(48*"#")
    while True:
        try:
            user_Input = int(input("Please select:"))
            if user_Input in [1,2]:
                break
        except ValueError:
            print("Please input 1 or 2 only!")
            continue
        
    if user_Input == 1:
        json_path = input("Please specifiy the absolute path of API json files folder: ")
        avi_postman_obj = avi_postman(file_dir = json_path)
        avi_postman_obj.generate_report()
    
    if user_Input == 2:
        target_file = input("Please specify the target single json file: ")
        avi_postman_obj = avi_postman(json_file=target_file)
        avi_postman_obj.ModifyJson(avi_postman_obj.json_data)
        avi_postman_obj.AddLogInOutRequest()
        avi_postman_obj.AddAnalyticsRequest()
        api_version = avi_postman_obj.SetVariables()
        # sort collection folder by name
        avi_postman_obj.json_data["item"] = sorted(avi_postman_obj.json_data["item"], key= operator.itemgetter("name"))

        print(f"condition1 Header changed count: {avi_postman_obj.count_cond1}, condition2 query change count: {avi_postman_obj.count_cond2}, condition3 auth removal count: {avi_postman_obj.count_cond3}")
        now = datetime.now() # current date and time
        date_time = now.strftime("%Y%m%d_%H%M")
        output_filename = f"Avi_{api_version}_Postman_collection_{date_time}.json"
        f2 = open(output_filename, "w")

        f2.write(json.dumps(avi_postman_obj.json_data, indent=4))
        #json.dump(data, f2,indent=4)