from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import datetime
from .config import GEMINI_API_KEY

class CalendarEvent(BaseModel):
    title: str = Field(description="El título del evento o tarea")
    start_time: str = Field(description="La hora de inicio del evento en formato ISO 8601 (ej., 2026-03-16T15:00:00+01:00)")
    end_time: str = Field(description="La hora de finalización del evento en formato ISO 8601 (ej., 2026-03-16T16:00:00+01:00)")
    description: str = Field(description="Detalles adicionales para añadir a la descripción del evento", default="")
    is_valid: bool = Field(description="¿El texto realmente contenía una tarea o cita válida?", default=True)

def parse_appointment_request(user_text: str) -> CalendarEvent | None:
    """
    Usa Google Gemini para analizar el lenguaje natural del usuario y convertirlo en un evento de calendario (CalendarEvent).
    """
    if not GEMINI_API_KEY:
        print("Advertencia: La variable GEMINI_API_KEY no está configurada.")
        return None
        
    client = genai.Client(api_key=GEMINI_API_KEY)

    now = datetime.datetime.now().isoformat()

    system_instruction = f"""
Eres un asistente personal encargado de agendar citas en un calendario.
El usuario te dará un mensaje de texto descriptivo en español.
La fecha y hora exacta actual de hoy es: {now}
Tu trabajo es extraer los detalles de la cita/tarea del texto del usuario.
Si no se da una duración explícita, asume una duración por defecto de 1 hora desde la hora de inicio.
Si el texto es solo un saludo o una conversación normal (ej. "Hola", "¿Qué tal?"), la variable is_valid debe ser falsa.
Devuelve los datos estructurados que coincidan con el esquema proporcionado.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CalendarEvent,
                temperature=0.1
            ),
        )
        # Convertir la respuesta de texto JSON al modelo automático de Pydantic
        event = CalendarEvent.model_validate_json(response.text)
        return event

    except Exception as e:
        print(f"Error al llamar a Gemini: {e}")
        return None
