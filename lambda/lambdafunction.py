import boto3
import os
import logging

# Initialize S3 client and logger.
s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # S3 Buckets
    input_bucket = 's3-pro3-rawbucket'
    output_bucket = 's3-pro3-processbucket'
    
    for record in event['Records']:
        try:
            # Extract file key
            file_key = record['s3']['object']['key']
            logger.info(f"Processing file: {file_key}")

            # Paths for temporary storage in Lambda
            download_path = f"/tmp/{os.path.basename(file_key)}"
            processed_path = f"/tmp/processed-{os.path.basename(file_key)}"

            # Download the file from the input bucket
            logger.info(f"Downloading file from bucket: {input_bucket}, key: {file_key}")
            s3.download_file(input_bucket, file_key, download_path)

            # Process the file (Example: Convert content to uppercase)
            with open(download_path, 'r') as infile, open(processed_path, 'w') as outfile:
                data = infile.read()
                outfile.write(data.upper())  # Transform to uppercase

            # Upload the processed file to the output bucket
            processed_key = f"processed-{os.path.basename(file_key)}"
            logger.info(f"Uploading processed file to bucket: {output_bucket}, key: {processed_key}")
            s3.upload_file(processed_path, output_bucket, processed_key)

            logger.info(f"Successfully processed and uploaded file: {processed_key}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_key}: {str(e)}")

    return {"statusCode": 200, "body": "File processed successfully"}

