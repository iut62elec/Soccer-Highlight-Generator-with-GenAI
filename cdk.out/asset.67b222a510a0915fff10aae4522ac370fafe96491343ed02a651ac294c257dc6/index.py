import json
import boto3
import pprint
import os
import time
def lambda_handler(event, context):
    print(event)
  
    
  
    
    client = boto3.client('mediaconvert')
    endpoint = client.describe_endpoints()['Endpoints'][0]['Url']
    print (endpoint)
    myclient = boto3.client('mediaconvert', endpoint_url=endpoint)
    
    
    # Check the status of MediaConvert jobs
    response1 = myclient.list_jobs(
        MaxResults=20,
        Order='DESCENDING',
        Status='PROGRESSING'
    )
    response2 = myclient.list_jobs(
        MaxResults=20,
        Order='DESCENDING',
        Status='SUBMITTED'
    )

    # Calculate the total number of active jobs
    active_jobs = len(response1['Jobs']) + len(response2['Jobs'])
    print(f"Number of active jobs: {active_jobs}")

    # Determine the status based on active jobs count
    if active_jobs > 0:
        # If there are active jobs, return NONCOMPLETE status
        status = 'NONCOMPLETE'
    else:
        # If there are no active jobs, return COMPLETE status
        status = 'COMPLETE'

    # Return the status
    print(f"Status: {status}")
    return status
    
    
    # a=3
    # while a>0:
        
    #     response1 = myclient.list_jobs(
    #     MaxResults=20,
    #     Order='DESCENDING',
    #     Status='PROGRESSING')
    #     response2 = myclient.list_jobs(
    #     MaxResults=20,
    #     Order='DESCENDING',
    #     Status='SUBMITTED')
    #     a=len(response1['Jobs'])+len(response2['Jobs'])
    #     print(response1)
    #     print(response2)
    #     print(a)
    #     time.sleep(5) 
    # Status='COMPLETE'
   
    # print(Status)
    
    # return Status #"checked job status" #json.dumps(response)
