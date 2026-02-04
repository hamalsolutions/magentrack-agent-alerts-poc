import logging
import json
import boto3
from typing import Dict, Any
from src.core.config import config

logger = logging.getLogger(__name__)

class LLMAgent:
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1' # Ideally config
        )
        self.model_id = config.BEDROCK_MODEL_ID

    def generate_response(self, alert: Dict[str, Any], guidance: str) -> str:
        """
        Generates a natural language response for the patient based on the alert and guidance.
        """
        prompt_context = f"""
        You are a helpful medical assistant chatbot for a clinic.
        
        GUIDANCE FOR THIS ALERT TYPE:
        {guidance}
        
        PATIENT ALERT DATA:
        Patient: {alert.get('patient_name')}
        Type: {alert.get('alert_type')}
        Value: {alert.get('value')}
        Time: {alert.get('timestamp')}
        
        INSTRUCTIONS:
        - Draft a short, empathetic, and clear WhatsApp message to the patient.
        - Do not include subject lines or placeholders.
        - Respond in the language appropriate for the context (Spanish/English mixed contexts often imply Spanish, but I will default to Spanish as per the architecture diagram 'Seguimiento' labels).
        """

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": prompt_context
                }
            ]
        })

        try:
            logger.info("Invoking Bedrock model...")
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            result_text = response_body.get("content")[0].get("text")
            return result_text.strip()
            
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}")
            # Fallback simple message if LLM fails
            return f"Hola {alert.get('patient_name')}, hemos detectado una alerta de {alert.get('alert_type')}. Por favor contáctenos."
