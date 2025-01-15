import boto3
import os
from botocore.exceptions import ClientError
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class CloudStorage:
    def __init__(self):
        try:
            logger.info(f"Initializing S3 client with region: {os.getenv('AWS_REGION')}")
            logger.info(f"Bucket name: {os.getenv('AWS_BUCKET_NAME')}")
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
            self.bucket_name = os.getenv('AWS_BUCKET_NAME')
            
            # Simple bucket existence check
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def upload_image(self, image_data: str, filename: str) -> str:
        """Upload base64 image to cloud storage and return public URL"""
        try:
            # Convert base64 to bytes
            image_bytes = base64.b64decode(image_data)
            file_key = f"blog-images/{filename}"

            # Direct upload approach
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Body=image_bytes,
                    ContentType='image/jpeg',
                    ACL='public-read'
                )
                logger.info(f"Successfully uploaded {filename}")
                
                # Return the URL
                url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file_key}"
                logger.info(f"Generated URL: {url}")
                return url

            except ClientError as e:
                error = e.response.get('Error', {})
                error_code = error.get('Code', 'Unknown')
                error_message = error.get('Message', str(e))
                logger.error(f"Upload failed with error {error_code}: {error_message}")
                return None

        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            return None 