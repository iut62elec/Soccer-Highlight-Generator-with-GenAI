import json
import boto3
def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    s3_cl = boto3.client('s3')

    # list all S3 buckets

    # iterate through each bucket and check if it starts with "sport"
    for bucket in s3.buckets.all():
        if bucket.name.startswith('soccer-'):

            # delete the bucket
            bucket.objects.all().delete()
            bucket.delete()
            
    dynamodb = boto3.client('dynamodb')

    # Get a list of all DynamoDB table names
    response = dynamodb.list_tables()
    table_names = response['TableNames']
    
    # Loop through all table names
    for table_name in table_names:
        # If the table name starts with "soccer-", delete the table
        if table_name.startswith('soccer-'):
            dynamodb.delete_table(TableName=table_name)        
            
            
    sqs = boto3.client('sqs')

    # Get a list of all SQS queue URLs
    response = sqs.list_queues()
    queue_urls = response['QueueUrls']
    
    # Loop through all queue URLs
    for queue_url in queue_urls:
        # Get the queue name from the queue URL
        queue_name = queue_url.split('/')[-1]
        # If the queue name starts with "soccer-", delete the queue
        if queue_name.startswith('soccer-'):
            sqs.delete_queue(QueueUrl=queue_url)        
    
    # queue_url = 'https://sqs.us-east-1.amazonaws.com/456667773660/sport_frames_files'

    # # Retrieve and delete messages in batches
    # while True:
    #     response = sqs.receive_message(
    #         QueueUrl=queue_url,
    #         AttributeNames=['All'],
    #         MaxNumberOfMessages=10,
    #         VisibilityTimeout=0,
    #         WaitTimeSeconds=0
    #     )
    
    #     messages = response.get('Messages', [])
    #     if not messages:
    #         break
    
    #     entries = [{'Id': msg['MessageId'], 'ReceiptHandle': msg['ReceiptHandle']} for msg in messages]
    #     response = sqs.delete_message_batch(QueueUrl=queue_url, Entries=entries)
    
    #     # Wait for all deletions to finish
    #     waiter = sqs.get_waiter('queue_empty')
    #     waiter.wait(QueueUrl=queue_url)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
