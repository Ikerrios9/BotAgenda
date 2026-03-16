import os
import httpx
from .config import WHATSAPP_TOKEN, WHATSAPP_NUMBER_ID

WHATSAPP_API_URL = f"https://graph.facebook.com/v19.0/{WHATSAPP_NUMBER_ID}/messages"

def extract_whatsapp_message(body: dict):
    """
    Extrae el número de teléfono del remitente y el texto del mensaje recibido en el webhook de WhatsApp.
    Devuelve (numero_remitente, texto) o (None, None) si no encuentra nada.
    """
    try:
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                if "messages" in value:
                    for message in value["messages"]:
                        # Número de teléfono del que envía el mensaje
                        from_number = message.get("from")
                        # Texto del mensaje
                        if message.get("type") == "text":
                            text = message.get("text", {}).get("body")
                            return from_number, text
    except Exception as e:
        print(f"Error procesando el mensaje de WhatsApp: {e}")
    return None, None

async def send_whatsapp_message(to: str, message_text: str):
    """
    Envía un mensaje de texto a un número de WhatsApp usando la API Oficial de Meta.
    El parámetro 'to' debe ser el número de teléfono con el código de país.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Error al enviar el mensaje de WhatsApp: {response.text}")
        return response.json()

