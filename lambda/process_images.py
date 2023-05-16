import boto3, urllib.parse

rekognition = boto3.client('rekognition', 'us-east-1')
table = boto3.resource('dynamodb').Table('user-tracking')

def get_faces(key):
    return table.get_item(Key={'User': key})

def detect_faces(bucket, key):
    index_response = rekognition.index_faces(
        Image={"S3Object": {"Bucket": bucket, "Name": key}}['Item']
    )

    face_list = [face['Face']['FaceId'] for face in index_response['FaceRecords']]
    db_response = get_faces(key)
    if db_response is None:
        face_count_map = {face: 1 for face in face_list}
        table.put_item(Item={
            'User': key,
            'Faces': face_count_map,
        })
    else:
        face_count_map = db_response['Faces']
        for face in face_list:
            if face_count_map[face] is not None:
                face_count_map[face] += 1 
            else:
                face_count_map[face] = 1
        table.update_item(
            Key={'User': key}, 
            UpdateExpression='Set Faces = :faces', 
            ExpressionAttributeValues={
                ':faces': face_count_map
            })
    return index_response


def lambda_handler(event, context):
    data = event['Records'][0]['s3']
    bucket = data['bucket']['name']
    key = urllib.parse.unquote_plus(data['object']['key'])
    try:
        response = detect_faces(bucket, key)
        print(response)
        return response
    except Exception as e:
        print(e)
        raise e