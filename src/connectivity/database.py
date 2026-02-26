import logging
import random
import boto3
import os
from typing import List, Dict, Any, Optional

# import psycopg2
# from psycopg2.extras import RealDictCursor
from src.core.config import config

logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")
MESSAGES_TABLE = os.environ.get("MESSAGES_TABLE")


def update_dynamodb_status(message_id, status):
    if not MESSAGES_TABLE:
        return
    try:
        table = dynamodb.Table(MESSAGES_TABLE)
        table.update_item(
            Key={"message_id": message_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": status},
        )
    except Exception as e:
        logger.error(f"Error updating DynamoDB: {e}")


class DatabaseAdapter:
    def __init__(self):
        self.connection = None

    def connect(self):
        """
        Establishes a connection to the database.
        Mocked for this POC if DB credentials are not reachable.
        """
        try:
            # self.connection = psycopg2.connect(
            #     host=config.DB_HOST,
            #     database=config.DB_NAME,
            #     user=config.DB_USER,
            #     password=config.DB_PASSWORD
            # )
            pass
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def fetch_pending_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches alerts with status 'PENDING'.
        """
        # Mock implementation for POC
        logger.info(f"Fetching up to {limit} pending alerts...")

        # In a real scenario:
        # with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
        #     cursor.execute("SELECT * FROM alerts WHERE status = 'PENDING' LIMIT %s", (limit,))
        #     return cursor.fetchall()

        # Returning mock data
        return (
            [
                {
                    "id": 1,
                    "patient_name": "Juan Perez",
                    "phone_number": "+1234567890",
                    "alert_type": "High Blood Pressure",
                    "value": "150/90",
                    "timestamp": "2023-10-27T10:00:00Z",
                    "status": "PENDING",
                }
            ]
            if random.random() > 0.5
            else []
        )

    def mark_alert_processed(self, alert_id: int):
        """
        Updates the alert status to 'PROCESSED'.
        """
        logger.info(f"Marking alert {alert_id} as PROCESSED")
        # In a real scenario:
        # with self.connection.cursor() as cursor:
        #     cursor.execute("UPDATE alerts SET status = 'PROCESSED' WHERE id = %s", (alert_id,))
        #     self.connection.commit()
