import json
import logging
import os
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

step_functions = boto3.client('stepfunctions')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

def lambda_handler(event, context):
    """
    Triggered by DynamoDB Stream.
    Starts the Step Function execution for new messages.
    """
    logger.info("Received event: %s", json.dumps(event))

    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            
            # Simple deserialization (for robust usage, use TypeDeserializer)
            message_id = new_image['message_id']['S']
            phone_number = new_image['phone_number']['S']
            message_text = new_image['message']['S']
            msg_type = new_image.get('type', {}).get('S', 'UNKNOWN')

            if msg_type != 'INCOMING':
                logger.info(f"Skipping non-incoming message: {message_id}")
                continue

            logger.info(f"Triggering workflow for message: {message_id}")
            
            input_data = {
                'message_id': message_id,
                'phone_number': phone_number,
                'message': message_text
            }

            try:
                step_functions.start_execution(
                    stateMachineArn=STATE_MACHINE_ARN,
                    name=f"Execution-{message_id}", # Ensure uniqueness or let AWS handle it
                    input=json.dumps(input_data)
                )
            except Exception as e:
                logger.error(f"Failed to start execution for {message_id}: {e}")
                # Depending on requirements, we might want to raise to retry via stream
    
    return {'status': 'success'}
