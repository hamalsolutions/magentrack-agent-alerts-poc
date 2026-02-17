import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    First step in Step Functions flow.
    Processes the message (e.g., validation, sentiment analysis, etc.)
    """
    logger.info("Processing message event: %s", json.dumps(event))
    
    # In a real scenario, we might add enrichment here.
    # For now, pass through.
    
    return event
