import boto3
import random
import string
import json
import os
#from botocore.vendored import requests

region=os.environ.get('REGION')

s3 = boto3.client('s3',region_name=region)
dynamodb = boto3.client('dynamodb')
sqs = boto3.client('sqs')
lambda_client = boto3.client('lambda')
dynamo = boto3.resource('dynamodb')


source_bucket_name=os.environ.get('VIDEO_ASSETS_BUCKET_NAME')


def lambda_handler(event, context):
    random_string=''.join(random.choice(string.ascii_lowercase) for i in range(10))
    entireInput = json.loads(event['entireInput'])
    file_name=entireInput['file_name']
    
    id=event['Executionid']
    final_highlight='none'
    final_original='none'
    status='Running'
    
    
    #######
    
    # table_name1='SFworkflow-2yumt4yc2raibewutmhs4p3qhi-dev'
    # table = dynamo.Table(table_name1)
    # print(event) 

    
    # # Write to DynamoDB table
    # table.put_item(
    #     Item={
    #         'id': id,
    #         'status': status,
    #         'final_highlight':final_highlight,
    #         'final_original': final_original
    #     }
    # )
    
    #####
    # Define the SQS queue name
    queue_name = 'soccer-'+ random_string
    
    if 1==1:
        # Create the SQS queue
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes={
                "VisibilityTimeout":"900",
                "MessageRetentionPeriod":"3600",
                "KmsMasterKeyId":""
            },
            
        )
        # Wait until the queue is created
        queue_url = response['QueueUrl']
        #waiter = sqs.get_waiter('queue_exists')
        #waiter.wait(QueueUrl=queue_url)

        # Get the ARN of the newly created SQS queue
        
        queue_attributes = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = queue_attributes['Attributes']['QueueArn']
        print(queue_arn)
        
        
        policy={
              "Version": "2008-10-17",
              "Id": "__default_policy_ID",
              "Statement": [
                {
                  "Sid": "__owner_statement",
                  "Effect": "Allow",
                  "Principal": {
                    "AWS": "arn:aws:iam::456667773660:root"
                  },
                  "Action": "SQS:*",
                  "Resource": queue_arn
                },
                {
                  "Sid": "example-statement-ID",
                  "Effect": "Allow",
                  "Principal": {
                    "Service": "s3.amazonaws.com"
                  },
                  "Action": "SQS:SendMessage",
                  "Resource": queue_arn
                }
              ]
            }
        
        response = sqs.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'Policy': json.dumps(policy)
                }
            )
        
       
        lambda_function_arn=os.environ.get('RECEIVE_MESSAGE_LAMBDA_ARN')
        lambda_function_name=lambda_function_arn.split(':')[-1]
        StatementId=f'{queue_name}-lambda',
    
        
        
       
        if 1==1:
            response = lambda_client.create_event_source_mapping(
                EventSourceArn=queue_arn,
                FunctionName=lambda_function_arn,
                Enabled=True,
                BatchSize=1
            )
            print(f'SQS trigger added to Lambda function {lambda_function_name}')
        # except:
        #     print('error')

    #####
    bucket_name ='soccer-'+ random_string
    if 1==1:
        # Generate a random bucket name
        #Create the S3 bucket
        bucket = s3.create_bucket(Bucket=bucket_name)
         # Wait until the bucket is created
        waiter = s3.get_waiter('bucket_exists')
        waiter.wait(Bucket=bucket_name)
        
        
        # Define the S3 event notification configuration
        event_notification_configuration = {
            'QueueConfigurations': [
                {
                    'Id': 's3-put-notification'+queue_name,
                    'QueueArn': queue_arn,
                    'Events': [
                        's3:ObjectCreated:Put'
                    ],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'prefix',
                                    'Value': 'Thumbnails/'
                                },
                                {
                                    'Name': 'suffix',
                                    'Value': '.jpg'
                                }
                            ]
                        }
                    }
                }
            ]
        }
       

        # Add the S3 event notification configuration to the bucket
        s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration=event_notification_configuration
        )
        
        
        #
        
        destination_bucket_name = bucket_name
    
        # Define the name of the file you want to copy
    
        # Create an S3 client object

        # Copy the file from the source bucket to the destination bucket
        copy_source = {
            'Bucket': source_bucket_name,
            'Key': 'public/'+file_name
        }
        s3.copy_object(CopySource=copy_source, Bucket=destination_bucket_name, Key=file_name)

        
    
    table_name = 'soccer-'+random_string

    if 1==1:
        # Generate a random table name
        params = {
            'TableName': table_name,
            'KeySchema': [
                {'AttributeName': 'filename', 'KeyType': 'HASH'},
                {'AttributeName': 'features', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'filename', 'AttributeType': 'S'},
                {'AttributeName': 'features', 'AttributeType': 'S'}
            ],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 100,
                'WriteCapacityUnits': 100
                                    }
         }
        table = dynamo.create_table(**params)
        # Wait until the table is created
        #waiter = dynamodb.meta.client.get_waiter('table_exists')
        #waiter.wait(TableName=table_name)
        table.wait_until_exists()
        print(f'Creating {table_name}')
    
    print('S3 bucket created: ', bucket_name)
    print('DynamoDB table created: ', table_name)

    #   
    return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!'),
            's3_bucket':bucket_name,
            'DDB_table':table_name,
            'queue_url':queue_url,
            'queue_arn':queue_arn,
            'vide_file_name':file_name
          
        }
    