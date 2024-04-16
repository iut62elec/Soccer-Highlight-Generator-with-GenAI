import json
import boto3

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    
    print(event) 
    try:
        id=event['Executionid']
    except:
        id='unknown'
  
    event_str = event['outputs']['Payload']
    event_payload = json.loads(event_str)  # Convert the JSON string back to a dictionary

    final_highlight = event_payload['final_highlight']
    final_original = event_payload['final_original']
    
    
    status='Succeeded'
    
    # # Write to DynamoDB table
    # table_name='SFworkflow-2yumt4yc2raibewutmhs4p3qhi-dev'
    # table = dynamodb.Table(table_name)
    # table.put_item(
    #     Item={
    #         'id': id,
    #         'status': status,
    #         'final_highlight':final_highlight,
    #         'final_original': final_original
    #     }
    # )
    
    response = {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Data saved successfully!'
        })
    }
    
    return response
