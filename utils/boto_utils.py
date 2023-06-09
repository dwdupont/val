import boto3
import os 

AWS_ACCESS_KEY = os.environ['AWS_KEY']
AWS_ACCESS_SECRET = os.environ['AWS_SECRET']


def get_text_from_s3(bucket_name, key) -> str:
    s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_ACCESS_SECRET)
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(key)
    response = obj.get()
    text = response['Body'].read()
    return text.decode()

