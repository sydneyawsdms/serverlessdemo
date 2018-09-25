import boto3
import json
import base64

# create the Rekognition boto3 client
rekognition_client=boto3.client('rekognition', region_name="ap-southeast-2")
 
def lambda_handler(event, context):
    # get the base64-encoded image from the event and convert it back to binary
    binary_image = base64.decodestring(event['picture'].encode())
    
    # make the call to RecognizeCelebrities API
    response = rekognition_client.recognize_celebrities(
        Image={
            'Bytes': binary_image
        }
    )

    print(response)
    
    # get the response from the API call and return only the first result
    if len(response['CelebrityFaces']) == 0:
        return {
            'name': None,
            'confidence': 'NaN'
        }
    else:
        return {
            'name': response['CelebrityFaces'][0]['Name'],
            'confidence': response['CelebrityFaces'][0]['MatchConfidence']
        }