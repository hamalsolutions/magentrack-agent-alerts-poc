import asyncio.proactor_events
import logging
import json
import boto3
from typing import Dict, Any
from src.core.config import config

logger = logging.getLogger(__name__)


class LLMAgent:
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",  # Ideally config
        )
        self.model_id = config.BEDROCK_MODEL_ID

    def generate_response(self, alert: Dict[str, Any], guidance: str) -> str:
        """
        Generates a natural language response for the patient based on the alert and guidance.
        """
        user_info = alert.get("user_info", {})
        alerts_summary = alert.get("alerts_summary", [])

        prompt_context = f"""
        Eres un asistente medico de una clinica.
        
        GUIA PARA ESTE TIPO DE ALERTA:
        {guidance}
        
        DATOS DE LA ALERTA DEL PACIENTE:
        Consulta: {alert.get("value")}
        Fecha: {alert.get("timestamp")}
        
        INFORMACION DEL PACIENTE:
        Genero: {user_info.get("Genero")}
        Edad: {user_info.get("Edad")}
        EstaEnEmbarazo: {user_info.get("EstaEnEmbarazo")}
        
        RESUMEN DE ALERTAS:
        {json.dumps(alerts_summary, indent=2, ensure_ascii=False)}
        
        INSTRUCCIONES:
        - Redacta un mensaje corto, empatico y claro para el paciente.
        - No incluyas lineas de asunto ni placeholders.
        - Responde en el idioma apropiado para el contexto.
        """

        conversation_history = alert.get("conversation_history", [])
        if conversation_history:
            history_text = "\n".join(
                [
                    f"[{msg['role']}] ({msg['timestamp']}): {msg['content']}"
                    for msg in conversation_history
                ]
            )
            prompt_context += f"\nHISTORIAL DE CONVERSACION RECIENTE:\n{history_text}\n"

        self.prompt = prompt_context

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt_context}],
            }
        )

        try:
            logger.info("Invoking Bedrock model...")
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json",
            )

            response_body = json.loads(response.get("body").read())
            result_text = response_body.get("content")[0].get("text")
            return result_text.strip()

        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}")
            # Fallback simple message if LLM fails
            return f"Hola {alert.get('patient_name')}, hemos detectado una alerta de {alert.get('alert_type')}. Por favor contáctenos."

    def extract_id_from_message(self, message_text: str) -> str:
        """
        Extracts the personal identification number from the user's message.
        """
        prompt_context = f"""
        You are an AI assistant. Your task is to extract the personal identification number (like national ID, passport, Cedula, etc.) from the user's message.
        Message: "{message_text}"
        
        If you find an ID number, output exactly the number as plain text with no other words or formatting.
        If you do not find an ID number, output "NONE".
        """
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": prompt_context}],
            }
        )
        try:
            logger.info("Invoking Bedrock for ID extraction...")
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            result_text = response_body.get("content")[0].get("text").strip()
            if result_text.upper() == "NONE":
                return None
            return result_text
        except Exception as e:
            logger.error(f"Failed to extract ID using AI: {e}")
            return None

    def evaluate_alert_state(
        self, alert_context: dict, conversation_history: list, guidance: str
    ) -> dict:
        ##format history for better formating without many brackets
        formated_history = "\n".join(
            [f"- {msg['role']}: {msg['content']}" for msg in conversation_history]
        )
        """
        Evalúa el contexto y devuelve una decisión en JSON puro.
        """
        prompt = f"""
        Eres un asistente médico inteligente. Analiza la siguiente alerta y la conversación previa del paciente.
        Debes decidir el 'estado' numérico (ej: 2) y una 'descripcion' corta para la alerta basada estrictamente en la siguiente guía:
        
        GUÍA PARA EL MANEJO DE ALERTAS:
        {guidance}
        
        Alerta: {json.dumps(alert_context, ensure_ascii=False)}
        Historial: 
        {formated_history}
        
        Si la guía proporcionada no contiene suficiente información para determinar un estado y descripción para esta alerta, utiliza por defecto el valor 2 para el estado y "Cerrado" para la descripción.
        
        Genera tu respuesta ÚNICAMENTE como un objeto JSON válido con la siguiente estructura y sin formato de markdown:
        {{
            "estado": <numero>,
            "descripcion": "<texto_corto>"
        }}
        """

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 150,
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "{"},
                ],
            }
        )

        try:
            logger.info("Invoking Bedrock model...")
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            result_text = response_body.get("content")[0].get("text")

            json_response = "{" + result_text.strip()

            if json_response.endswith("```"):
                json_response = json_response.replace("```", "")

            decision = json.loads(json_response)
            return decision

        except json.JSONDecodeError as e:
            logger.error(
                f"Fallo al parsear JSON del LLM: {e}. Texto fallback: {result_text}"
            )
            return {"estado": 2, "descripcion": "2"}
        except Exception as e:
            logger.error(f"Error evaluando estado en LLM: {e}")
            return {"estado": 2, "descripcion": "2"}
