import json
import logging
import os
import uuid
from datetime import datetime
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('MESSAGES_TABLE','')

def lambda_handler(event, context):
    """
    Handler for API Gateway triggers.
    Receives a message and stores it in DynamoDB.
    """
    logger.info("Received event: %s", json.dumps(event))

    try:
        body = json.loads(event.get('body', '{}'))
        
        # Basic validation
        if 'message' not in body or 'phone_number' not in body:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing message or phone_number'})
            }

        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'message_id': message_id,
            'phone_number': body['phone_number'],
            'message': body['message'],
            'timestamp': timestamp,
            'status': 'RECEIVED',
            'type': 'INCOMING'
        }
        
        if not TABLE_NAME:
            logger.error("TABLE_NAME environment variable is not set")
            raise ValueError("TABLE_NAME environment variable is not set")

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=item)
        
        logger.info(f"Message {message_id} stored successfully.")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message received', 'message_id': message_id})
        }

    except Exception as e:
        logger.error(f"Error processing input: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
