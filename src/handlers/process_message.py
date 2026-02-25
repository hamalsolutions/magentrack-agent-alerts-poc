from datetime import timedelta
from datetime import datetime
import json
import logging
import os
import urllib.request
import urllib.parse
import urllib.error
from src.core.llm_agent import LLMAgent

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

llm_agent = LLMAgent()

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


def fetch_patient_user_info(id_number, retry=True) -> dict | None:
    try:
        url = f"{MAGENTRACK_BACKEND_URL}/Paciente/GetPaginationPacientes?$inlinecount=0&$skip=0&$top=20&$search={urllib.parse.quote(id_number)}"

        headers = {"Accept": "application/json"}
        token = get_magentrack_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get(
                "Items", data.get("items", data if isinstance(data, list) else [])
            )
            if items and len(items) > 0:
                first_item = items[0]
                return {
                    "PatientId": first_item.get("PatientId"),
                    "Genero": first_item.get("Genero"),
                    "Edad": first_item.get("Edad"),
                    "EstaEnEmbarazo": first_item.get("EstaEnEmbarazo"),
                }
    except urllib.error.HTTPError as e:
        if e.code == 401 and retry:
            logger.warning(
                "Token expired or unauthorized (401). Retrying with a fresh token..."
            )
            global cached_token
            cached_token = None
            return fetch_patient_user_info(id_number, retry=False)
        else:
            logger.error(f"HTTPError fetching patient user info for {id_number}: {e}")
    except Exception as e:
        logger.error(f"Failed to fetch patient user info for {id_number}: {e}")
    return None


def fetch_alerts(user_id: int, endpoint: str, retry: bool = True):
    try:
        url = f"{MAGENTRACK_BACKEND_URL}{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        token = get_magentrack_token()
        now = datetime.now().isoformat()
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        body = {"PacienteId": user_id, "FechaInicio": yesterday, "FechaLimite": now}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            url, method="POST", headers=headers, data=json.dumps(body).encode("utf-8")
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            # 0	Abierto, 1 En seguimiento, 2 Cerrado, 3 Expirado, 4 No gestionado
            data = [
                item
                for item in data
                if item.get("Estado") == 0 or item.get("Estado") == 1
            ]
            return data
    except urllib.error.HTTPError as e:
        if e.code == 401 and retry:
            logger.warning(
                "Token expired or unauthorized (401). Retrying with a fresh token..."
            )
            global cached_token
            cached_token = None
            return fetch_alerts(user_id, endpoint, retry=False)
        else:
            logger.error(
                f"HTTPError fetching alerts from {endpoint} for user {user_id}: {e}"
            )
    except Exception as e:
        logger.error(f"Failed to fetch alerts from {endpoint} for user {user_id}: {e}")
    return None


def lambda_handler(event, context):
    """
    First step in Step Functions flow.
    Processes the message (LLM identity extraction + Magentrack queries)
    """
    logger.info("Processing message event: %s", json.dumps(event))

    message_text = event.get("message", "")

    # Extract identity
    id_number = llm_agent.extract_id_from_message(message_text)
    logger.info(f"Extracted ID number: {id_number}")

    user_id = None
    user_info = None
    alerts = {}

    if id_number:
        user_info = fetch_patient_user_info(id_number)
        if user_info:
            user_id = user_info.get("PatientId")
            logger.info(f"Fetched User ID from API: {user_id}")

    if user_id:
        bascula = fetch_alerts(user_id, "/Paciente/GetAlertasBascula")
        glucometro = fetch_alerts(user_id, "/Paciente/GetAlertasGlucometro")
        oximetro = fetch_alerts(user_id, "/Paciente/GetAlertasOximetro")
        tensiometro = fetch_alerts(user_id, "/Paciente/GetAlertasTensiometro")

        alerts = {
            "bascula": bascula,
            "glucometro": glucometro,
            "oximetro": oximetro,
            "tensiometro": tensiometro,
        }

    # Enrich the event with new data
    event["id_number"] = id_number
    event["user_id"] = user_id
    event["user_info"] = user_info
    event["alerts"] = alerts

    return event
