import json
import logging
import os
import uuid
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
import boto3
from src.core.llm_agent import LLMAgent

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
llm_agent = LLMAgent()

TABLE_NAME = os.environ.get('MESSAGES_TABLE','')
MAGENTRACK_BACKEND_URL = os.environ.get('MAGENTRACK_BACKEND_URL', 'https://api.magentrack.com')
MAGENTRACK_USER = os.environ.get('MAGENTRACK_USER', '')
MAGENTRACK_PASSWORD = os.environ.get('MAGENTRACK_PASSWORD', '')

cached_token = None

def get_magentrack_token():
    global cached_token
    if cached_token:
        return cached_token

    auth_url = f"{MAGENTRACK_BACKEND_URL}/Usuarios/GetToken"
    body = {
        "Correo": MAGENTRACK_USER,
        "Password": MAGENTRACK_PASSWORD
    }

    try:
        req = urllib.request.Request(
            auth_url,
            method='POST',
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_response = response.read().decode('utf-8')
            try:
                data = json.loads(raw_response)
                # handle if it is a dictionary
                cached_token = data.get("token", data.get("Token", data.get("access_token", raw_response)))
            except json.JSONDecodeError:
                # handle if it is a raw string
                cached_token = raw_response.strip('"')
            return cached_token
    except Exception as e:
        logger.error(f"Failed to fetch Magentrack token: {e}")
        return None


def fetch_patient_user_id(id_number, retry=True):
    try:
        url = f"{MAGENTRACK_BACKEND_URL}/Paciente/GetPaginationPacientes?$inlinecount=0&$skip=0&$top=20&$search={urllib.parse.quote(id_number)}"
        
        headers = {'Accept': 'application/json'}
        token = get_magentrack_token()
        if token:
            headers['Authorization'] = f"Bearer {token}"
            
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            items = data.get('Items', data.get('items', data if isinstance(data, list) else []))
            if items and len(items) > 0:
                first_item = items[0]
                #Later on we can include more user information (Genero, Edad, EstaEnEmbarazo, FechaUltimaMenstruacion)
                user_id = first_item.get('PatientId')
                return user_id
    except urllib.error.HTTPError as e:
        if e.code == 401 and retry:
            logger.warning("Token expired or unauthorized (401). Retrying with a fresh token...")
            global cached_token
            cached_token = None
            return fetch_patient_user_id(id_number, retry=False)
        else:
            logger.error(f"HTTPError fetching patient user ID for {id_number}: {e}")
    except Exception as e:
        logger.error(f"Failed to fetch patient user ID for {id_number}: {e}")
    return None


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
        
        message_text = body['message']
        id_number = llm_agent.extract_id_from_message(message_text)
        logger.info(f"Extracted ID number: {id_number}")
        
        user_id = None
        if id_number:
            user_id = fetch_patient_user_id(id_number)
            logger.info(f"Fetched User ID from API: {user_id}")
        
        item = {
            'message_id': message_id,
            'phone_number': body['phone_number'],
            'message': message_text,
            'timestamp': timestamp,
            'status': 'RECEIVED',
            'type': 'INCOMING'
        }
        
        if user_id:
            item['user_id'] = user_id
        
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
