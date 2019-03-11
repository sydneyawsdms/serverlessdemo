import boto3
from botocore.config import Config
import os
import json
import time
import logging
import threading
import copy
from boto3.dynamodb.conditions import Attr,Key

log = logging.getLogger()
log.setLevel(logging.INFO)

table = boto3.resource('dynamodb').Table(os.environ['Connections_Table'])
translate_client = boto3.client('translate', region_name='us-east-1')
comprehend_client = boto3.client('comprehend')

management_api = ""

def ws_connect(connection_id, nickname = ""):
    log.info('New connection established: {}'.format(connection_id))
    item = {'connectionId': connection_id}
    if len(nickname) != 0:
        item['nickname'] = nickname
    broadcast_message(connection_id, {'nickname': nickname, 'message': "Joined the chatroom"})
    response = table.put_item(Item = item)
    return {'statusCode': response['ResponseMetadata']['HTTPStatusCode']}
    

def ws_disconnect(connection_id):
    log.info('Deleting connection {}'.format(connection_id))
    nicknames = table.scan(
        ProjectionExpression='nickname',
        FilterExpression=Key("connectionId").eq(connection_id)
    )
    response = table.delete_item(
        Key={
            'connectionId': connection_id
        }
    )
    if len(nicknames[u'Items'])!=0:
        nickname = nicknames[u'Items'][0]['nickname']
    else:
        nickname = ""
    broadcast_message(connection_id, {'nickname': nickname, 'message': "left the chatroom"})
    return response['ResponseMetadata']

def broadcast_message(current_connectId, post_data):
    connections = table.scan(
        ProjectionExpression='connectionId'
    )
    threadList = []
    for item in connections['Items']:
        connection_id = item['connectionId']
        messagepayload = copy.deepcopy(post_data);
        if connection_id == current_connectId:
            messagepayload['nickname'] = 'You'
        t = threading.Thread(target=send_single_message, args=(connection_id, messagepayload))
        t.setDaemon(True)
        t.start()
        threadList.append(t)
    for thread in threadList:
        thread.join()


def send_single_message(connection_id,  messagepayload):
    messagepayload['timestamp'] = time.time();
    try:
        management_api.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(messagepayload)
        )
    except Exception as e:
        log.info('Error posting data: {}'.format(e.response['Error']))
        if e.response['Error']['Code'] == '410':
            log.info('Found stale connection')
            ws_disconnect(connection_id)


def ws_message(eventRequestContext, eventBody):
    body = json.loads(eventBody)
    post_data = {
        'message': body['message']
    }

    if body['translate'] == True:
        try:
            translate_response = translate_client.translate_text(
                Text=body['message'],
                SourceLanguageCode='auto',
                TargetLanguageCode='en'
            )
            if translate_response['ResponseMetadata']['HTTPStatusCode'] == 200:
                post_data['message'] = translate_response['TranslatedText']
        except Exception as e:
            log.info('Can not translate the input')

    if body['sentiment'] == True:
        comprehend_response = comprehend_client.detect_sentiment(
            LanguageCode='en',
            Text=post_data['message']
        )
        post_data['sentiment'] = comprehend_response['Sentiment']

    post_data['nickname'] = body.get('nickname','')

    if body['message'].startswith('@'):
        to_name = body['message'].split(" ")[0][1:]
        post_data['message'] = " ".join(post_data['message'].split(" ")[1:])
        connections = table.scan(
            ProjectionExpression='connectionId',
            FilterExpression=Attr("nickname").eq(to_name)
        )
        for connection in connections[u'Items']:
            send_single_message(connection[u'connectionId'], post_data)
    else:
        broadcast_message(eventRequestContext['connectionId'], post_data)
    return {'statusCode': 200}


def lambda_handler(event, context):
    print(event)
    global management_api
    if management_api == "":
        endpoint_url = 'https://{}/{}'.format(event['requestContext']['domainName'], event['requestContext']['stage'])
        config = Config(
            retries={'max_attempts': 1},
            read_timeout=5,
            connect_timeout=5
        )
        management_api = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url, config=config)
    if event['requestContext']['eventType'] == 'CONNECT':
        if 'queryStringParameters' in event:
            nickname = event['queryStringParameters']['nickname']
        else:
            nickname = ""
        response = ws_connect(event['requestContext']['connectionId'], nickname)
        return response

    if event['requestContext']['eventType'] == 'DISCONNECT':
        response = ws_disconnect(event['requestContext']['connectionId'])
        return {'statusCode': response['HTTPStatusCode']}

    if event['requestContext']['eventType'] == 'MESSAGE':
        response = ws_message(event['requestContext'], event['body'])
        return response
    #We should never reach here
    return {'statusCode': 404}

