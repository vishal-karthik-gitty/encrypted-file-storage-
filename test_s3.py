import os
import boto3
from dotenv import load_dotenv
load_dotenv()

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='ap-south-1'
)

bucket_name = "secure-file-storage-project1"

s3.upload_file('app.py', bucket_name, 'test_app.py')