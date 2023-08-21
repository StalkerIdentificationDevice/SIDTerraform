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

def get_facial_hair_description(face_detail: dict):
    facial_hair_description = 'no noticable facial hair'
    if face_detail['Beard']['Value'] and face_detail['Mustache']['Value']:
        facial_hair_description = 'a beard and mustache'
    elif face_detail['Beard']['Value'] :
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
        CollectionId=user_id,
        DetectionAttributes=['GENDER', 'BEARD', 'AGE_RANGE', 'MUSTACHE']
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
        num_sightings = len(timestamp_list)
        if num_sightings >= 5:
            fifth_last_timestamp = datetime.strptime(timestamp_list[-5], '%Y%m%dT%H%M%S')
            current_timestamp = datetime.strptime(timestamp, '%Y%m%dT%H%M%S')
            difference_in_seconds = (current_timestamp - fifth_last_timestamp).total_seconds()
            if difference_in_seconds < 1800:
                send_push_message(device_token, "Possible Follower Alert", {
                    'description': db_response['Description'],
                    'num_sightings': num_sightings
                })
  

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
    key_path_only = str(key).removesuffix('.jpg')
    key_sections = key_path_only.split('/')
    user_id = key_sections[0]
    device_token = key_sections[1]
    timestamp = key_sections[2]
    try:
        detect_and_process_faces(bucket, user_id, key, timestamp, device_token)
    except Exception as e:
        print(e)
        raise e
