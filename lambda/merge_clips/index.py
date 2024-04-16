import json
import boto3
import time
import os


MP4output='HighlightClips'
client = boto3.client('mediaconvert')
endpoint = client.describe_endpoints()['Endpoints'][0]['Url']
myclient = boto3.client('mediaconvert', endpoint_url=endpoint)
r=os.getenv("MEDIA_CONVERT_ROLE_ARN") 

def lambda_handler(event, context):
    #large_clip_counter=1;
    #if large_clip_counter >1:
    
    s3=boto3.client('s3')
    import math

    print(type(event))
    print('-----------------')
    if 1==1:
      #time.sleep(10) #sleep for 5 seconds to wait for some previous job to complete

      

      prefix='High';postfix='final.mp4'
      bucket_name=event['s3_bucket']
      table_name=event['DDB_table']
      file_name=event['vide_file_name']
      queue_url=event['queue_url']
      queue_arn=event['queue_arn']
      bucket=bucket_name
      filelist=s3.list_objects(Bucket=bucket)['Contents']
      mp4files = [file['Key'] for file in filelist if file['Key'][-9:]==postfix if file['Key'][:4]==prefix]
          
    if len(mp4files) >1:
          
        s3 = boto3.resource('s3')
        snslinks=[]
        hyperlink_format = '<a href="{link}">{text}</a>'
          
          
        
      
        with open('mediaconvert_setting.json') as f:
                data = json.load(f)
                
        data["Settings"]["OutputGroups"][0]["OutputGroupSettings"]["FileGroupSettings"]["Destination"]=f"s3://{bucket}/HighlightClips/"
        
       
        counter=0;
        print(mp4files)
        print(type(mp4files))
        print(mp4files[0].split('from-')[1].split('-to')[0])
        mp4files=sorted(mp4files, key=lambda x: int(x.split('from-')[1].split('-to')[0]))
        #mp4files = sorted(mp4files)
    
        print(mp4files)
        large_clip_counter=0
        if 1==1:
          for key in mp4files[:]:
              #print(key,counter)
              counter=counter+1;
              if counter<150:
                data['Settings']['Inputs'].append({
                "AudioSelectors": {
                  "Audio Selector 1": {
                    "DefaultSelection": "DEFAULT"
                  }
                },
                "VideoSelector": {},
                "TimecodeSource": "ZEROBASED",
                "FileInput": 's3://'+bucket+'/'+key
                        })
               
              else:
                #print(data['Settings']['Inputs'])
                data["Settings"]["OutputGroups"][0]["CustomName"]='highlight'+str(counter)
                print(data["Settings"])
                response = myclient.create_job(
                  Role=r,
                  Settings=data['Settings'])
                large_clip_counter=large_clip_counter+1;  
                counter=0
                with open('mediaconvert_setting.json') as f:
                  data = json.load(f)
                data["Settings"]["OutputGroups"][0]["OutputGroupSettings"]["FileGroupSettings"]["Destination"]=f"s3://{bucket}/HighlightClips/"
  
          print(data["Settings"])
          response = myclient.create_job(
                  Role=r,
                  Settings=data['Settings'])
          large_clip_counter=large_clip_counter+1        
    else:
    
        ###just copy the file as highlight 
        print("only one file")
        source=bucket+'/'+ mp4files[0]
        key1=mp4files[0].replace('.mp4','highlight.mp4')
        print(key1,bucket,mp4files[0],source)
        
        response = s3.copy_object(
        Bucket=bucket,
        CopySource=source,
        Key=key1
        )

    return json.dumps({"filesmerged":mp4files})
   
