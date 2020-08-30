import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('dce_db.content')

def write_db(user_name, key, content, image_path):	
    #Generate a unique identifier which will be used as the Pk in DB
    identifier = str(uuid.uuid1())
   
    # DynamoDB query to write  
    table.put_item(
        Item = {
                'user_name':user_name,
                'key': key,
                'content': content,
                'image_path':image_path,
                'uuid': identifier
        }
    )
    
    return "Write query success"