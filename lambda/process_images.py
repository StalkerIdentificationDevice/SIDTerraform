import boto3, urllib.parse
from datetime import datetime
from exponent_server_sdk import (
    PushClient,
    PushMessage,
)

rekognition = boto3.client('rekognition', 'us-east-1')
table = boto3.resource('dynamodb').Table('user-tracking')
s3 = boto3.client('s3', 'us-east-1')


def get_faces(user_id, face_id):
    return table.get_item(Key={'UserId': user_id, 'FaceId': face_id}).get('Item')

def get_facial_hair_description(face_detail):
    facial_hair_description = 'no noticable facial hair'
    if face_detail['Beard']['Value'] and face_detail['Mustache']['Value']:
        facial_hair_description = 'a beard and mustache'
    elif face_detail['Beard']['Value']:
        facial_hair_description = 'a beard'
    elif face_detail['Mustache']['Value']:
        facial_hair_description = 'a mustache'
    return facial_hair_description


def detect_and_process_faces(bucket, user_id, key, timestamp, device_token):
    print("Bucket: " + bucket)
    print("Key: " + key)
    
    try:
        print(str(rekognition.describe_collection(CollectionId=user_id)))
    except:
        rekognition.create_collection(CollectionId=user_id)
    
    index_response = rekognition.index_faces(
        Image={"S3Object": {"Bucket": bucket, "Name": key}},
        CollectionId=user_id
    )
    
    print("Index faces response:", str(index_response))
    
    for face in index_response['FaceRecords']:
        search_results = rekognition.search_faces(CollectionId=user_id, FaceId=face['Face']['FaceId'], MaxFaces=1).get('FaceMatches')
        if search_results is not None and len(search_results) == 1:
            rekognition.delete_faces(CollectionId=user_id, FaceIds=[face['Face']['FaceId']])
            process_face(user_id, search_results[0].get('Face')['FaceId'], face['FaceDetail'], timestamp, device_token, bucket, key)
        else:
            process_face(user_id, face['Face']['FaceId'], face['FaceDetail'], timestamp, device_token, bucket, key)


def process_face(user_id, face_id, face_detail, timestamp, device_token, bucket, key):
    db_response = get_faces(user_id, face_id)    
    print("DB response: ", str(db_response))
    if db_response is None:
        facial_hair_description = get_facial_hair_description(face_detail)
        table.put_item(Item={
            'UserId': user_id,
            'FaceId': face_id,
            "Timestamps": [timestamp],
            "Description": 'A {} between {} and {} with {}'.format(
                face_detail['Gender']['Value'], 
                face_detail['AgeRange']['Low'], 
                face_detail['AgeRange']['High'],
                facial_hair_description)
        })
    else:
        timestamp_list = list(db_response['Timestamps'])
        timestamp_list.append(timestamp)
        table.update_item(
            Key={'UserId': user_id, "FaceId": face_id}, 
            UpdateExpression='Set Timestamps = :times', 
            ExpressionAttributeValues={
                ':times': timestamp_list
            })
        if len(timestamp_list) >= 5:
            fifth_last_timestamp = datetime.strptime(timestamp_list[-5], '%Y%m%dT%H%M%S')
            current_timestamp = datetime.strptime(timestamp, '%Y%m%dT%H%M%S')
            difference_in_seconds = (current_timestamp - fifth_last_timestamp).total_seconds()
            if difference_in_seconds < 1800:
                send_push_message(device_token, "{} has been seen behind you 10 times within the last 30 minutes".format(db_response['Description']))
  

def send_push_message(token, message, extra=None):
    try:
        response = PushClient().publish(
            PushMessage(to=token,
                        body=message,
                        data=extra))
        print(response)
    except Exception as e:
        print(e)


def lambda_handler(event, context):
    data = event['Records'][0]['s3']
    bucket = data['bucket']['name']
    key = urllib.parse.unquote_plus(data['object']['key'])
    user_id = str(key).split('/')[0]
    device_token = str(key).split('/')[1]
    timestamp = str(key).split('/')[2].removesuffix('.jpg')
    try:
        detect_and_process_faces(bucket, user_id, key, timestamp, device_token)
    except Exception as e:
        print(e)
        raise e
    
if __name__ == '__main__':
    event = {
    "Records": [
        {
        "eventVersion": "2.0",
        "eventSource": "aws:s3",
        "awsRegion": "us-east-1",
        "eventTime": "1970-01-01T00:00:00.000Z",
        "eventName": "ObjectCreated:Put",
        "userIdentity": {
            "principalId": "EXAMPLE"
        },
        "requestParameters": {
            "sourceIPAddress": "127.0.0.1"
        },
        "responseElements": {
            "x-amz-request-id": "EXAMPLE123456789",
            "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
        },
        "s3": {
            "s3SchemaVersion": "1.0",
            "configurationId": "testConfigRule",
            "bucket": {
            "name": "sid-user-public-photo-data20230721034631063100000001",
            "ownerIdentity": {
                "principalId": "EXAMPLE"
            },
            "arn": "arn:aws:s3:::sid-user-public-photo-data20230721034631063100000001"
            },
            "object": {
            "key": "34883468-6081-70c6-3617-fb90ea22dc33%2FExponentPushToken[ymOqA3JhS0m6ypCAjQgSaI]%2F20230730T205903.jpg",
            "size": 1024,
            "eTag": "0123456789abcdef0123456789abcdef",
            "sequencer": "0A1B2C3D4E5F678901"
            }
        }
        }
    ]
    }
    lambda_handler(event, None)