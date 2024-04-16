import json
import boto3
import pprint
import os

def lambda_handler(event, context):
    sqs_client = boto3.client('sqs')
    #input_data = json.loads(event['Input'])
    print(event)
    bucket_name=event['s3_bucket']
    table_name=event['DDB_table']
    file_name=event['vide_file_name']
    queue_url=event['queue_url']
    queue_arn=event['queue_arn']

    response = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages'])
    ApproximateNumberOfMessages=response['Attributes']['ApproximateNumberOfMessages']
    print('ApproximateNumberOfMessages',response['Attributes']['ApproximateNumberOfMessages'])
    
    Status='Default'
    if ApproximateNumberOfMessages=='0':
        Status='COMPLETE'
    return Status #"checked job status" #json.dumps(response)
