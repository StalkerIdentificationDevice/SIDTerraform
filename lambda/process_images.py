import boto3, urllib.parse
from datetime import datetime
import io
from PIL import Image, ImageDraw
import json

rekognition = boto3.client('rekognition', 'us-east-1')
table = boto3.resource('dynamodb').Table('user-tracking')
s3 = boto3.client('s3', 'us-east-1')
sns = boto3.client('sns')

platform_application_arn = 'arn:aws:sns:us-east-1:837111542380:app/APNS/S.I.D'


def get_faces(user_id, face_id):
    return table.get_item(Key={'UserId': user_id, 'FaceId': face_id}).get('Item')


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
            process_face(user_id, search_results[0].get('Face')['FaceId'], face['FaceDetail'], timestamp, device_token, bucket, key)
            rekognition.delete_faces(CollectionId=user_id, FaceIds=[face['Face']['FaceId']])
        else:
            process_face(user_id, face['Face']['FaceId'], face['FaceDetail'], timestamp, device_token, bucket, key)


def process_face(user_id, face_id, face_detail, timestamp, device_token, bucket, key):
    db_response = get_faces(user_id, face_id)    
    print("DB response: ", str(db_response))
    if db_response is None:
        table.put_item(Item={
            'UserId': user_id,
            'FaceId': face_id,
            "Timestamps": [timestamp],
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
            # If this face has been seen 5 times in last 30 minutes
            if difference_in_seconds < 1800:
                send_notification(device_token, face_detail, "Safety Alert", "A face has been seen behind you 5 times within the last 30 minutes", bucket, key)
  
                    
def send_notification(device_token, face_detail, title, body, bucket, key):
    arn = get_endpoint_arn(device_token)
    message = {
    "aps": {
        "alert": {
            "title": title,
            "body": body
        },
        "badge": 1,
        "sound": "default"
    },
    "data": {
        "message_id": "12345",
        "sender_id": "67890"
    }
}
    # message = message + get_image_url(bucket, key, face_detail)
    sns.publish(TargetArn=arn, Message=json.dumps(message), MessageStructure='json')


# def get_image_url(bucket, key, face_detail):
#     s3_response = s3.get_object(Bucket=bucket, Key=key)
#     stream = io.BytesIO(s3_response['Body'].read())
#     image = Image.open(stream)
    
#     img_width, img_height = image.size
#     draw = ImageDraw.Draw(image)
    
#     box = face_detail['BoundingBox']
#     left = img_width * box['Left']
#     top = img_height * box['Top']
#     width = img_width * box['Width']
#     height = img_height * box['Height']

#     points = (
#         (left, top),
#         (left + width, top),
#         (left + width, top + height),
#         (left, top + height),
#         (left, top)

#     )
#     draw.line(points, fill='#00d400', width=2)
#     colored_picture = s3.put_object()
#     s3.generate_presigned_url('get_object')
#     return image.tobytes()


def get_endpoint_arn(device_token):
    endpoints_obj = sns.list_endpoints_by_platform_application(platform_application_arn)
    endpoints_list = endpoints_obj['Endpoints']
    for endpoint in endpoints_list:
        if endpoint['Attributes']['Token'] is device_token:
            return endpoint['EndpointArn']
    return sns.create_platform_endpoint(PlatformApplicationArn=platform_application_arn, Token=device_token)['EndpointArn']


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