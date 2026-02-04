import logging
import boto3
from botocore.exceptions import ClientError
from src.core.config import config

logger = logging.getLogger(__name__)

class S3Adapter:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = config.S3_BUCKET_NAME

    def get_guidance_document(self, key: str = "guidelines.txt") -> str:
        """
        Retrieves the guidance document from S3.
        """
        if not self.bucket_name:
            logger.warning("S3 Bucket Name not set. Returning default guidance.")
            return "Please respond politely to the patient regarding their health alert."

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            logger.error(f"Failed to fetch guidance from S3: {e}")
            return "Error retrieving guidance."
