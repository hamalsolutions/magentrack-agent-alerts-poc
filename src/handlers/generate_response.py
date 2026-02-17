import json
import logging
import os
import boto3
from datetime import datetime
from src.core.config import config
from src.core.llm_agent import LLMAgent
from src.connectivity.s3_store import S3Adapter

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('MESSAGES_TABLE')

def lambda_handler(event, context):
    """
    Second step in Step Functions flow.
    Generates a response using LLM and stores it in DynamoDB.
    """
    logger.info("Generating response for event: %s", json.dumps(event))

    message_id = event.get('message_id')
    phone_number = event.get('phone_number')
    user_message = event.get('message')

    try:
        s3 = S3Adapter()
        agent = LLMAgent()
        
        guidance = s3.get_guidance_document()
        
        context_data = {
            'patient_name': 'Unknown',
            'alert_type': 'User Query',
            'value': user_message,
            'timestamp': datetime.utcnow().isoformat(),
            'phone_number': phone_number
        }
        
        response_text = agent.generate_response(context_data, guidance)
        
        table = dynamodb.Table(TABLE_NAME)
        
        response_item = {
            'message_id': f"resp-{message_id}",
            'original_message_id': message_id,
            'phone_number': phone_number,
            'message': response_text,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'GENERATED',
            'type': 'OUTGOING'
        }
        
        table.put_item(Item=response_item)
        logger.info(f"Response stored for {message_id}")
        
        return {
            'status': 'success',
            'response': response_text,
            'original_message_id': message_id
        }

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise e
