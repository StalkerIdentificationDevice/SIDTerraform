import boto3, urllib.parse

rekognition = boto3.client('rekognition', 'us-east-1')
table = boto3.resource('dynamodb').Table('user-tracking')
s3 = boto3.client('s3', 'us-east-1')

def get_faces(key):
    return table.get_item(Key={'User': key}).get('Item')

def detect_faces(bucket, key):
    print("Bucket: " + bucket)
    print("Key: " + key)
    folder = str(key).split('/')[0]
    
    # Test
    s3.get_object(Bucket=bucket, Key=key)
    
    try:
        print(str(rekognition.describe_collection(CollectionId=folder)))
    except:
        rekognition.create_collection(CollectionId=folder)
    
    index_response = rekognition.index_faces(
        Image={"S3Object": {"Bucket": bucket, "Name": key}},
        CollectionId=folder
    )
    
    print("Index faces response:", str(index_response))

    face_list = [face['Face']['FaceId'] for face in index_response['FaceRecords']]
    db_response = get_faces(folder)
    
    print("DB response: ", str(db_response))
    if db_response is None:
        face_count_map = {face: 1 for face in face_list}
        table.put_item(Item={
            'User': folder,
            'Faces': face_count_map,
        })
    else:
        face_count_map = dict(db_response['Faces'])
        for face in face_list:
            if face_count_map.get(face) is not None:
                face_count_map[face] += 1 
            else:
                face_count_map[face] = 1
        table.update_item(
            Key={'User': folder}, 
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