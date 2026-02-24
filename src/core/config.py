import os
from dataclasses import dataclass
try:
    from dotenv import load_dotenv
    # Cargar variables desde el archivo .env si existe
    load_dotenv()
except ImportError:
    pass

class Config:
    # Database
    @property
    def DB_HOST(self) -> str:
        return os.getenv("DB_HOST", "localhost")
        
    @property
    def DB_NAME(self) -> str:
        return os.getenv("DB_NAME", "postgres")
        
    @property
    def DB_USER(self) -> str:
        return os.getenv("DB_USER", "postgres")
        
    @property
    def DB_PASSWORD(self) -> str:
        return os.getenv("DB_PASSWORD", "password")
    
    # Twilio (WhatsApp)
    @property
    def TWILIO_ACCOUNT_SID(self) -> str:
        return os.getenv("TWILIO_ACCOUNT_SID", "")
        
    @property
    def TWILIO_AUTH_TOKEN(self) -> str:
        return os.getenv("TWILIO_AUTH_TOKEN", "")
        
    @property
    def TWILIO_WHATSAPP_NUMBER(self) -> str:
        return os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    
    # AWS
    @property
    def S3_BUCKET_NAME(self) -> str:
        return os.getenv("S3_BUCKET_NAME", "")
        
    @property
    def BEDROCK_MODEL_ID(self) -> str:
        return os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

    # App
    @property
    def POLLING_BATCH_SIZE(self) -> int:
        return int(os.getenv("POLLING_BATCH_SIZE", "10"))

config = Config()
