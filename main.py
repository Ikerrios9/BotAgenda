from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
import os

# Cargar las variables de entorno primero
load_dotenv()

# Importar los servicios después de cargar las variables de entorno
from services.whatsapp_service import extract_whatsapp_message, send_whatsapp_message
from services.gemini_service import parse_appointment_request
from services.calendar_service import create_calendar_event

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "mi_token_botagenda_2026")

app = FastAPI(title="BotAgenda WhatsApp")

@app.get("/")
def read_root():
    return {"status": "BotAgenda is running"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Endpoint para verificación inicial de WhatsApp Meta Cloud.
    WhatsApp enviará un GET req con tokens para validar este endpoint.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return int(challenge)
        else:
            return {"error": "Verificación fallida"}

    return {"error": "Petición no válida"}

async def process_message_background(sender_number: str, message_text: str):
    print(f"Procesando mensaje de {sender_number}: {message_text}")
    # 1. Analizar el mensaje con Gemini
    event_data = parse_appointment_request(message_text)
    
    if not event_data or not event_data.is_valid:
        await send_whatsapp_message(sender_number, "No he detectado ninguna tarea o cita concreta para añadir al calendario.")
        return

    # 2. Crear evento en Google Calendar
    desc = event_data.description
    if desc:
        desc += "\n\n(Añadido por BotAgenda)"
    else:
        desc = "(Añadido por BotAgenda)"

    success, result = create_calendar_event(
        title=event_data.title, 
        start_time=event_data.start_time, 
        end_time=event_data.end_time, 
        description=desc
    )

    # 3. Responder al usuario en WhatsApp
    if success:
        reply_text = f"✅ ¡Listo! Guardado en tu calendario: '{event_data.title}'.\nTe he puesto la alarma de 30 minutos antes."
    else:
        reply_text = f"❌ Hubo un error al guardarlo en el calendario: {result}"

    await send_whatsapp_message(sender_number, reply_text)


@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint principal para recibir mensajes entrantes de WhatsApp.
    Maneja el procesamiento en segundo plano para evitar bloqueos por tiempo de espera de Meta.
    """
    body = await request.json()

    # Extraer texto y remitente
    sender_number, message_text = extract_whatsapp_message(body)

    if sender_number and message_text:
        # Se envía a un proceso en segundo plano porque Meta exige devolver un HTTP 200 en menos de 20s
        background_tasks.add_task(process_message_background, sender_number, message_text)
        
    return {"status": "ok"}
