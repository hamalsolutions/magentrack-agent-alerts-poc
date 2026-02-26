import json
import logging
import os
import urllib.request
import urllib.parse
from datetime import datetime

from src.core.llm_agent import LLMAgent
from src.connectivity.s3_store import S3Adapter
from src.connectivity.database import update_dynamodb_status

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAGENTRACK_BACKEND_URL = os.environ.get(
    "MAGENTRACK_BACKEND_URL", "https://api.magentrack.com"
)
MAGENTRACK_USER = os.environ.get("MAGENTRACK_USER", "")
MAGENTRACK_PASSWORD = os.environ.get("MAGENTRACK_PASSWORD", "")

cached_token = None


def get_magentrack_token():
    global cached_token
    if cached_token:
        return cached_token

    auth_url = f"{MAGENTRACK_BACKEND_URL}/Usuarios/GetToken"
    body = {"Correo": MAGENTRACK_USER, "Password": MAGENTRACK_PASSWORD}
    try:
        req = urllib.request.Request(
            auth_url,
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_response = response.read().decode("utf-8")
            try:
                data = json.loads(raw_response)
                cached_token = data.get(
                    "token", data.get("Token", data.get("access_token", raw_response))
                )
            except json.JSONDecodeError:
                cached_token = raw_response.strip('"')
            return cached_token
    except Exception as e:
        logger.error(f"Failed to fetch Magentrack token: {e}")
        return None


def lambda_handler(event, context):
    """
    Third step in Step Functions flow.
    Evaluates the message and alerts, then decides what state to put the alert in.
    """
    logger.info("Processing alert event: %s", json.dumps(event))
    message_id = event.get("original_message_id")
    user_id = event.get("user_id", 0)
    alerts = event.get("alerts", {})
    conversation_history = event.get("conversation_history", [])

    s3 = S3Adapter()
    guidance = s3.get_guidance_document("alert_handling_guidelines.txt")

    agent = LLMAgent()

    decision = agent.evaluate_alert_state(
        alert_context={"alerts": alerts},
        conversation_history=conversation_history,
        guidance=guidance,
    )
    logger.info(f"Decision: {decision}")

    estado = decision.get("estado", 2)
    description = str(decision.get("descripcion", "Cerrado"))

    token = get_magentrack_token()

    for category, cat_alerts in alerts.items():
        if not cat_alerts:
            continue

        for alert in cat_alerts:
            endpoint = ""
            body = {}

            if category == "bascula":
                endpoint = "/Paciente/CreateNotaAlertaBascula"
                body = {
                    "Descripcion": description,
                    "PacienteId": user_id,
                    "AlertaBasculaAlertaId": alert.get("AlertaBasculaAlertaId", 0),
                    "Estado": estado,
                    "Token": token or "",
                }
            elif category == "glucometro":
                endpoint = "/Paciente/CreateNotaAlertaGlucometro"
                body = {
                    "Descripcion": description,
                    "PacienteId": user_id,
                    "AlertaGlucometroAlertaId": alert.get(
                        "AlertaGlucometroAlertaId", 0
                    ),
                    "Token": token or "",
                    "Estado": estado,
                    "Latitud": alert.get("Latitud", 0),
                    "Longitud": alert.get("Longitud", 0),
                }
            elif category == "oximetro":
                endpoint = "/Paciente/CreateNotaAlertaOximetro"
                body = {
                    "Descripcion": description,
                    "PacienteId": user_id,
                    "AlertaOximetroAlertaId": alert.get("AlertaOximetroAlertaId", 0),
                    "Estado": estado,
                    "Token": token or "",
                }
            elif category == "tensiometro":
                endpoint = "/Paciente/CreateNotaAlertaTensiometro"
                body = {
                    "NotaId": alert.get("NotaId", 0),
                    "Descripcion": description,
                    "PacienteId": user_id,
                    "Estado": estado,
                    "NombreUsuario": "system",
                    "FechaCreacion": datetime.utcnow().isoformat() + "Z",
                    "IndiceNota": alert.get("IndiceNota", 0),
                }

            if endpoint:
                url = f"{MAGENTRACK_BACKEND_URL}{endpoint}"
                headers = {
                    "Content-Type": "application/json",
                }
                if token:
                    headers["Authorization"] = f"Bearer {token}"

                try:
                    ## TODO: THIS IS RETURNING 400 REVIEW THE BODY
                    req = urllib.request.Request(
                        url,
                        method="POST",
                        data=json.dumps(body).encode("utf-8"),
                        headers=headers,
                    )
                    with urllib.request.urlopen(req, timeout=10) as _:
                        logger.info(f"Successfully sent note to {endpoint}")
                except Exception as e:
                    logger.error(f"Failed to send note to {endpoint}: {e}")

    # After that update the alert status in dynamo DB to CLOSED.
    # Assuming the instructions mean closing the message status in MESSAGES_TABLE.
    if message_id:
        # Note, the messages_table might contain the user message or the response message.
        # We will update the original message.
        update_dynamodb_status(message_id, "CLOSED")

    return {"status": "success", "message": "Alerts handled successfully"}
