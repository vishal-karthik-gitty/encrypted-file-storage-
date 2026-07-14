import boto3
import os

s3 = boto3.client(
    's3',
    aws_access_key_id="",
    aws_secret_access_key="",
    region_name='ap-south-1'
)

bucket_name = "secure-file-storage-project1"

s3.upload_file('app.py', bucket_name, 'test_app.py')

print("Uploaded to S3 ✅")