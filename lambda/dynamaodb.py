import boto3
import os
import logging
from datetime import datetime

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB Table Name
DYNAMODB_TABLE = "processed-data-table"

def lambda_handler(event, context):
    input_bucket = 's3-pro3-rawbucket'
    output_bucket = 's3-pro3-processbucket'
    
    for record in event['Records']:
        try:
            # Extract file key
            file_key = record['s3']['object']['key']
            logger.info(f"Processing file: {file_key}")

            # Check if file exists in S3 before processing
            try:
                s3.head_object(Bucket=input_bucket, Key=file_key)
                logger.info(f"File {file_key} exists in {input_bucket}, proceeding...")
            except Exception as e:
                logger.error(f"File {file_key} not found: {str(e)}")
                return {"statusCode": 404, "body": f"File {file_key} not found in S3"}

            # Paths for temporary storage in Lambda
            download_path = f"/tmp/{os.path.basename(file_key)}"
            processed_path = f"/tmp/processed-{os.path.basename(file_key)}"

            # Download the file from the input bucket
            s3.download_file(input_bucket, file_key, download_path)

            # Process the file (Placeholder: Simply copying)
            with open(download_path, 'rb') as infile, open(processed_path, 'wb') as outfile:
                outfile.write(infile.read())  

            # Upload the processed file to the output bucket
            processed_key = f"processed-{os.path.basename(file_key)}"
            s3.upload_file(processed_path, output_bucket, processed_key)
            logger.info(f"Uploaded processed file: {processed_key}")

            # ✅ Store metadata in DynamoDB
            table = dynamodb.Table(DYNAMODB_TABLE)
            table.put_item(
                Item={
                    'file_id': file_key,  # ✅ Ensure Partition Key (file_id) is present
                    'upload_timestamp': int(datetime.utcnow().timestamp()),  # ✅ Convert timestamp to Number
                    'processed_file_name': processed_key,
                    'bucket_name': input_bucket,
                    'processed_bucket_name': output_bucket,
                    'status': 'processed'
                }
            )
            logger.info(f"Metadata stored in DynamoDB for {file_key}")

        except Exception as e:
            logger.error(f"Error processing file {file_key}: {str(e)}")

    return {"statusCode": 200, "body": "File processed and metadata stored successfully"}
