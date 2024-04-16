import json
import boto3
import time
import os


MP4output='HighlightClips'
client = boto3.client('mediaconvert')
endpoint = client.describe_endpoints()['Endpoints'][0]['Url']
myclient = boto3.client('mediaconvert', endpoint_url=endpoint)

snsarn=os.getenv("TOPIC_ARN")
client_sns = boto3.client('sns')

CF_endpoint='https://'+os.environ.get('CLOUDFRONT_ENDPOINT_URL') 
Amplify_bucket=os.environ.get('VIDEO_ASSETS_BUCKET_NAME')


def lambda_handler(event, context):
    
    s3=boto3.client('s3')
    import math

    print(type(event))
    print('-----------------')
    bucket_name=event['s3_bucket']
    table_name=event['DDB_table']
    file_name=event['vide_file_name']
    queue_url=event['queue_url']
    queue_arn=event['queue_arn']
    
    
    
    bucket=bucket_name
    prefix='High';postfix='highlight.mp4'
    filelist=s3.list_objects(Bucket=bucket)['Contents']
    mp4files = [file['Key'] for file in filelist if file['Key'][-13:]==postfix if file['Key'][:4]==prefix]
    
    
    source=bucket+'/'+ mp4files[0]
    key1='public/'+ mp4files[0].replace('finalhighlight.mp4','HL.mp4')
    print(key1,bucket,mp4files[0],source)
    
    response = s3.copy_object(
    Bucket=bucket,
    CopySource=source,
    Key=key1
    )
    
    response2 = s3.copy_object(
    Bucket=Amplify_bucket,
    CopySource=source,
    Key=key1
    )
    
    key2='public/HighlightClips/'+file_name
    source2=bucket+'/'+ file_name

    response2 = s3.copy_object(
    Bucket=Amplify_bucket,
    CopySource=source2,
    Key=key2
    )
    
    final_name=mp4files[0].replace('finalhighlight.mp4','HL.mp4').split('HighlightClips/')[1]
    final_highlight=CF_endpoint+final_name
    final_original=CF_endpoint+file_name

    final_highlight=CF_endpoint+'/public/HighlightClips/'+final_name
    final_original=CF_endpoint+'/public/HighlightClips/'+file_name
    
    
    message={"final_highlight":final_highlight,
    "final_original":final_original
        
    }
    sns_response = client_sns.publish(TargetArn=snsarn,Message=json.dumps({'default': json.dumps(message)}),MessageStructure='json')
    
    return json.dumps(message)
          