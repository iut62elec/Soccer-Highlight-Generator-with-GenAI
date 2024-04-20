import json
import boto3
import time
from boto3.dynamodb.conditions import Key, Attr
import math 
import os


r=os.getenv("MEDIA_CONVERT_ROLE_ARN") 


MP4output='HighlightClips'
client = boto3.client('mediaconvert')
endpoint = client.describe_endpoints()['Endpoints'][0]['Url']
myclient = boto3.client('mediaconvert', endpoint_url=endpoint)

def start_mediaconvert_job(data, sec_in, sec_out,bucket_name,file_name):
    print('CLIPPING : '+ str(sec_in) + '--------------->>>' + str(sec_out))
    s3=bucket_name;v=file_name
    data['Settings']['Inputs'][0]['FileInput']='s3://'+s3+'/'+v
    print(data['Settings']['Inputs'][0]['FileInput'])
    data['Settings']['OutputGroups'][0]['OutputGroupSettings']['FileGroupSettings']['Destination']='s3://'+s3+'/'+MP4output+'/'
    
    starttime = time.strftime('%H:%M:%S:00', time.gmtime(sec_in))
    print(starttime)
    endtime = time.strftime('%H:%M:%S:00', time.gmtime(sec_out))
    
    data['Settings']['Inputs'][0]['InputClippings'][0] = {'EndTimecode': endtime, 'StartTimecode': starttime}
    #print(data['Settings']['Inputs'][0]['InputClippings'][0])
    
    data['Settings']['OutputGroups'][0]['Outputs'][0]['NameModifier'] = '-from-'+str(sec_in)+'-to-'+str(sec_out)
    
    response = myclient.create_job(
    Role=r,
    Settings=data['Settings'])

def lambda_handler(event, context):
    #print(input_data)
    bucket_name=event['s3_bucket']
    table_name=event['DDB_table']
    file_name=event['vide_file_name']
    queue_url=event['queue_url']
    queue_arn=event['queue_arn']
    
    ddtable=table_name;s3=bucket_name;v=file_name

    # TODO DYNAMO DB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(ddtable)
    response = table.scan() 
    
    timeins = []
    timeouts=[]
    dict1={}
    for i in response['Items']:
        if(i['pickup']=='yes'):
            
            timeins.append(i['timeins'])
            timeouts.append(i['timeouts'])
            dict1[i['filename']]=i['timeins']
    print(dict1)

    sortedDict = sorted(dict1)
    print(sortedDict)

    sortedDict1 = sorted(dict1.items(), key=lambda x:x[1])
    print(sortedDict1)


            
    print("timeins*******")
    print(timeins)
    print("timeouts*******")
    print(timeouts)
    timeins = sorted([int(float(x)) for x in timeins])

    timeouts =sorted([int(float(x)) for x in timeouts])
    print("timeins after sort*******")
    ##[5800, 5850, 5900, 5950, 6000, 6050, 6100, 6150, 6200, 6250, 6300, 6350, 6400, 6450, 6700, 6800, 6850, 6900, 6950, 7000, 7050, 7100, 7150, 7200, 7250, 7300, 7350, 7400]

    print(timeins)
    print("timeouts after sort*******")
    print(timeouts)
    print("Min timein:{}".format(min(timeins)))
    print("MAx timeouts:{}".format(min(timeouts)))
    mintime =min(timeins)
    maxtime =max(timeouts)
    
    print('mintime='+str(mintime))
    print('maxtime='+str(maxtime))
    
    print(timeins)
    print(timeouts)
    mystarttime = mintime
    #
    
    if 1==1:
        # TODO MEDIACONVERT
        buffer1=2 #5 #1sec
        start_sec=math.floor(timeins[0]/1000)
        with open('mediaconvert_setting.json') as f:
            data = json.load(f)
        begin=1    
        for time1 in timeins[0:]:
            #print('time1:',time1)
            if begin==1:
               sec_in=math.floor(time1/1000)
               begin=0;
            else:
                pass
                
            if (sec_in + buffer1) > math.floor(time1/1000):
                pass
            else:
                #sec_out=math.floor(time1/1000)  
                sec_out=sec_in + buffer1
                
                print('new clip',sec_in,sec_out)
                start_mediaconvert_job(data, sec_in, sec_out,bucket_name,file_name)
                #time.sleep(1)
                #begin=1
                sec_in=math.floor(time1/1000)
        sec_out=math.ceil(time1/1000)
        if sec_in!=sec_out:
            print('new clip',sec_in,sec_out)
            start_mediaconvert_job(data, sec_in, sec_out,bucket_name,file_name)
        #sec_in = 5
        #sec_out = 8
        #start_mediaconvert_job(data, sec_in, sec_out)
        #time.sleep(1)
    
    
    return json.dumps({'bucket':s3,'prefix':'High','postfix':'mp4'})
