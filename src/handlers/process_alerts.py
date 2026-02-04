import logging
from src.core.config import config
from src.connectivity.database import DatabaseAdapter
from src.connectivity.whatsapp import WhatsAppAdapter
from src.connectivity.s3_store import S3Adapter
from src.core.llm_agent import LLMAgent

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main Lambda entry point triggered by EventBridge Schedule.
    """
    logger.info("Starting Alert Processing Cycle")
    
    # Initialize Adapters
    db = DatabaseAdapter()
    s3 = S3Adapter()
    whatsapp = WhatsAppAdapter()
    agent = LLMAgent()

    processed_count = 0
    
    try:
        db.connect()
        alerts = db.fetch_pending_alerts(limit=config.POLLING_BATCH_SIZE)
        
        if not alerts:
            logger.info("No pending alerts found.")
            return {"status": "success", "processed": 0}

        # Fetch guidance (assuming global guidance for POC)
        guidance = s3.get_guidance_document()

        for alert in alerts:
            try:
                alert_id = alert.get("id")
                patient_phone = alert.get("phone_number")
                
                logger.info(f"Processing alert {alert_id} for {alert.get('patient_name')}")
                
                # 1. Generate Response
                message_text = agent.generate_response(alert, guidance)
                
                # 2. Send via WhatsApp
                whatsapp.send_message(to=patient_phone, text=message_text)
                
                # 3. Mark as Processed
                db.mark_alert_processed(alert_id)
                
                processed_count += 1
                
            except Exception as item_error:
                logger.error(f"Error processing alert {alert.get('id')}: {item_error}")
                # Continue processing other alerts even if one fails
                continue

    except Exception as e:
        logger.error(f"Critical execution error: {e}")
        return {"status": "error", "message": str(e)}
    
    logger.info(f"Cycle completed. Processed {processed_count} alerts.")
    return {"status": "success", "processed": processed_count}

if __name__ == "__main__":
    # Local test execution
    lambda_handler({}, None)
