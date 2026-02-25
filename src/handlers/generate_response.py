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

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("MESSAGES_TABLE")


def extract_alert_data(alert: dict, category: str) -> dict:
    data = {
        "Prioridad": alert.get("Prioridad"),
        "NombreAlerta": alert.get("NombreAlerta"),
        "TipoMedicion": alert.get("TipoMedicion"),
        "FechaAlerta": alert.get("FechaAlerta"),
    }

    if category == "bascula" and alert.get("Bascula"):
        b_data = alert["Bascula"]
        data["Peso"] = b_data.get("Peso")
        data["Talla"] = b_data.get("Talla")
        data["Imc"] = b_data.get("Imc")
        if "EsEmbarazada" in b_data:
            data["EsEmbarazada"] = b_data.get("EsEmbarazada")
    elif category == "glucometro":
        data["NivelGlucosa"] = alert.get("NivelGlucosa")
        data["Limite"] = alert.get("Limite")
    elif category == "tensiometro":
        data["PASD"] = alert.get("PASD")

    return {k: v for k, v in data.items() if v is not None}


def lambda_handler(event, context):
    """
    Second step in Step Functions flow.
    Generates a response using LLM and stores it in DynamoDB.
    """
    logger.info("Generating response for event: %s", json.dumps(event))

    message_id = event.get("message_id")
    phone_number = event.get("phone_number")
    user_message = event.get("message")
    user_info = event.get("user_info") or {}
    alerts = event.get("alerts") or {}

    try:
        s3 = S3Adapter()
        agent = LLMAgent()

        guidance = s3.get_guidance_document()

        mapped_alerts = []
        for category, cat_alerts in alerts.items():
            if cat_alerts:
                for alert in cat_alerts:
                    mapped_alerts.append(extract_alert_data(alert, category))

        context_data = {
            "alert_type": "User Query",
            "value": user_message,
            "timestamp": datetime.utcnow().isoformat(),
            "phone_number": phone_number,
            "user_info": {
                "Genero": "Masculino" if user_info.get("Genero") == 0 else "Femenino",
                "Edad": user_info.get("Edad"),
                "EstaEnEmbarazo": "Si"
                if user_info.get("EstaEnEmbarazo") == 1
                else "No",
            },
            "alerts_summary": mapped_alerts,
        }

        response_text = agent.generate_response(context_data, guidance)

        table = dynamodb.Table(TABLE_NAME)

        response_item = {
            "prompt": agent.prompt,
            "message_id": f"resp-{message_id}",
            "original_message_id": message_id,
            "phone_number": phone_number,
            "message": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "GENERATED",
            "type": "OUTGOING",
        }

        table.put_item(Item=response_item)
        logger.info(f"Response stored for {message_id}")

        return {
            "status": "success",
            "response": response_text,
            "original_message_id": message_id,
            "user_id": event.get("user_id"),
            "alerts": alerts,
        }

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise e
