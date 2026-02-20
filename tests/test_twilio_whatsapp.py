import sys
import os

# TEST PARA PROBAR LA CONEXIÓN CON TWILIO WHATSAPP

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.connectivity.whatsapp import WhatsAppAdapter
from src.core.config import config

def test_connection():
    print("--- Probando Conexión con Twilio WhatsApp ---")
    
    # 1. Verificador variables
    if not config.TWILIO_ACCOUNT_SID or not config.TWILIO_AUTH_TOKEN:
        print("❌ ERROR: No se detectaron las credenciales de Twilio.")
        print("Asegúrate de configurar TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en tu .env")
        return

    print(f"Cuenta Twilio: ...{config.TWILIO_ACCOUNT_SID[-4:]}")
    print(f"Número Remitente: {config.TWILIO_WHATSAPP_NUMBER}")
    
    # 2. Instancia el adaptador
    adapter = WhatsAppAdapter()
    
    # 3. Pedir destino
    target = input("Introduce el número de destino (ej: +5491122334455): ")
    
    # 4. Se envia
    print(f"Enviando mensaje a {target}...")
    adapter.send_message(target, "¡Hola! Esta es una prueba de Magentrack usando Twilio.")

if __name__ == "__main__":
    test_connection()
