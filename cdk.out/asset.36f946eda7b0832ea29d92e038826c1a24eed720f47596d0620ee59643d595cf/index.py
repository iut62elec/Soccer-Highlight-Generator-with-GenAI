import boto3
import json
import math
import os
import base64

import boto3
import io
ssm = boto3.client('ssm')
s3 = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-1')

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
sqs_client = boto3.client('sqs')
client_rek=boto3.client('rekognition')


def lambda_handler(event, context):
  
    s3_event_message = json.loads(event['Records'][0]['body'])
    bucket_name = s3_event_message['Records'][0]['s3']['bucket']['name']
    # Retrieve the parameter value from Parameter Store and parse it as JSON
    response = ssm.get_parameter(Name=bucket_name, WithDecryption=False)
    #print(bucket_name,response)
    my_json_str = response['Parameter']['Value']
    config_json = json.loads(my_json_str)

    
    bucket_name=config_json['bucket_name']
    table_name=config_json['table_name']
    table = dynamodb.Table(table_name)


    file=event['Records'][0]['body']
    #print(type(file))
    #print(file)
    file=file.split("key")[1].split(",")[0].replace('":"',"").replace('"',"")
    #print(file)
 
    if 1==1:
        #for file in master_filename_list[:]:
        #outevent['filename'] = file
        #bucket=bucket_name
        #photo=file
       

        # Get Object in S3
        response = s3.get_object(Bucket=bucket_name, Key=file)
        image_content = response['Body'].read()
    
        # Encoding images to base64
        base64_encoded_image = base64.b64encode(image_content).decode('utf-8')
        
   
    
        prompt="""
        Begin a meticulous inspection of the soccer game image at hand. Examine each aspect within the frame closely to identify and catalogue visible elements. Concentrate on pinpointing the location of the players, the soccer ball, and most importantly, the soccer goal — defined as the structure composed of the goalposts and the net. It is vital to distinguish the soccer goal from the field's white markings, such as midfield lines or sidelines. The classification is straightforward: an image is marked as 'Highlight' if the soccer goal is clearly present, without any consideration of the event's context or your knowledge of the game's significance. In contrast, if the soccer goal is not visible, classify the image as 'Normal'. Additionally, any frame that does not display the soccer field should be automatically labeled as 'Normal' as well. Focus purely on object presence within the image for categorization, adhering strictly to the visible inclusion of the entire soccer goal to determine a 'Highlight', independent of any other activity taking place on the field. Again, The soccer goal must be fully visible, including both goalposts and the entire net between them, to be classified as a 'Highlight'. Your final response for each analysis should be a single word: 'Normal' or 'Highlight'.
        """
        
       
        
        
        # Create payloads for Bedrock Invoke, and can change model parameters to get the results you want.
        payload = {
            "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "top_k": 250,
                "top_p": 0.999,
                "temperature": 0,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_encoded_image
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
        }
        
        # Convert the payload to bytes
        body_bytes = json.dumps(payload['body']).encode('utf-8')
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            body=body_bytes,
            contentType=payload['contentType'],
            accept=payload['accept'],
            modelId=payload['modelId']
        )
        
        # Process the response
        response_body = json.loads(response['body'].read())
        result = response_body['content'][0]['text']
        
        #print(result)
        #print("Custom labels detected: " + str(label_count))
        #print(response1)
        #feature1=result
        # try:
        #     feature1=result
        # except:
        #     feature1='Normal'
        # #print(file)
        # ####
        
        pickup='no'
        if result=='Highlight':
            pickup='yes'
        #FramerateNumerator=10    
        #FramerateNumerator=10    
        FramerateNumerator=1    
        #FramerateNumerator=2    
        time_parm=1000/FramerateNumerator  ##originally  FramerateNumerator was 20 then param was 50
        #timeins=str(int(file.split('.')[1])*50);timeouts=str(1 + int(file.split('.')[1])*50)
        timeins=str(int(file.split('.')[1])*time_parm);timeouts=str(1 + int(file.split('.')[1])*time_parm)
        #response = table.put_item(Item={'filename':file, 'features':feature1})
        response = table.put_item(Item={'filename':file, 'features':result, 'pickup':pickup, 'timeins':timeins, 'timeouts':timeouts})

      
