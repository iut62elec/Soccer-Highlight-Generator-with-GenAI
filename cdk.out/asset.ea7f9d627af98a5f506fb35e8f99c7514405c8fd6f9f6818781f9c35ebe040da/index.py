import json
import boto3
import os
import boto3
ssm = boto3.client('ssm')

r=os.getenv("MEDIA_CONVERT_ROLE_ARN") 

def lambda_handler(event, context):

    with open('mediaconvert_setting.json') as f:
            data = json.load(f)
    
    print(event)
    bucket_name=event['s3_bucket']
    table_name=event['DDB_table']
    file_name=event['vide_file_name']
    s3=bucket_name
    v=file_name
    my_config = {
        "bucket_name":event['s3_bucket'],
        "table_name":event['DDB_table'],
        "file_name":event['vide_file_name'],
        "queue_url":event['queue_url'],
        "queue_arn":event['queue_arn']
    }
    
    my_json_str = json.dumps(my_config)
    
    # Set the parameter value in Parameter Store
    ssm.put_parameter(
        Name=event['s3_bucket'],
        Value=my_json_str,
        Type='String',
        Overwrite=True
    )
    
        

    
    client=boto3.client('mediaconvert')
    endpoint=client.describe_endpoints()['Endpoints'][0]['Url']
    myclient=boto3.client('mediaconvert', endpoint_url=endpoint)
    data['Settings']['Inputs'][0]['FileInput']='s3://'+s3+'/'+v               
    data['Settings']['OutputGroups'][0]['OutputGroupSettings']['FileGroupSettings']['Destination']='s3://'+s3+'/MP4/'
    data['Settings']['OutputGroups'][1]['OutputGroupSettings']['FileGroupSettings']['Destination']='s3://'+s3+'/Thumbnails/'
    #print(data)
    #print(type(data))
    response = myclient.create_job(Role=r,Settings=data['Settings'])
    print(response)
    return "done"
