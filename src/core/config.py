import os
from dataclasses import dataclass

@dataclass
class Config:
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    
    # WhatsApp
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    
    # AWS
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

    # App
    POLLING_BATCH_SIZE: int = int(os.getenv("POLLING_BATCH_SIZE", "10"))

config = Config()
